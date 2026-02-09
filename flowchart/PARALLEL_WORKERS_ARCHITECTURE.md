# 4-Worker Parallel Processing Architecture

## Overview
The system now supports **4-worker parallel processing** for Character-based video production with staggered browser initialization and asynchronous login.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     MASTER_MANAGER.PY                            │
│                   (Main Orchestrator)                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ├── Sequential Mode (--type character)
                       │   └──> Single SharedSessionManager
                       │       └──> CharacterVideoManager
                       │
                       └── Parallel Mode (--type character --parallel)
                           │
                           ▼
                    ┌─────────────────┐
                    │ _init_workers() │
                    │ (4 workers)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┬────────────────┐
        │                    │                    │                │
        ▼                    ▼                    ▼                ▼
   Worker 0              Worker 1            Worker 2         Worker 3
   ┌──────────┐         ┌──────────┐        ┌──────────┐     ┌──────────┐
   │ Browser  │         │ Browser  │        │ Browser  │     │ Browser  │
   │ (Fresh)  │         │ (Fresh)  │        │ (Fresh)  │     │ (Fresh)  │
   └────┬─────┘         └────┬─────┘        └────┬─────┘     └────┬─────┘
        │                    │                    │                │
   SharedSession        SharedSession        SharedSession   SharedSession
        │                    │                    │                │
        ├─ DreaminaGen       ├─ DreaminaGen       ├─ DreaminaGen  ├─ DreaminaGen
        └─ Veo3Gen           └─ Veo3Gen           └─ Veo3Gen      └─ Veo3Gen
```

---

## Worker Initialization Flow

### Phase 0: Worker Creation (Lines 206-210 in master_manager.py)

```
START: User runs --parallel flag
  │
  ▼
[STEP 1] Print: "[MODE] Using 4-Worker Parallel Processing"
  │
  ▼
[STEP 2] Call: _init_workers(num_workers=4, stagger_delay=10)
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│              WORKER INITIALIZATION LOOP                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Worker 0:                                              │
│    - Open fresh Chrome profile                          │
│    - Create DreaminaGenerator                           │
│    - Create DreaminaVideoGenerator                      │
│    - Submit login to background thread                   │
│    - Print: "[WORKER 0] Browser opened"                │
│    - WAIT 10 SECONDS                                    │
│                                                          │
│  Worker 1:                                              │
│    - Open fresh Chrome profile                          │
│    - Create DreaminaGenerator                           │
│    - Create DreaminaVideoGenerator                      │
│    - Submit login to background thread                   │
│    - Print: "[WORKER 1] Browser opened"                │
│    - WAIT 10 SECONDS                                    │
│                                                          │
│  Worker 2:                                              │
│    - Open fresh Chrome profile                          │
│    - Create DreaminaGenerator                           │
│    - Create DreaminaVideoGenerator                      │
│    - Submit login to background thread                   │
│    - Print: "[WORKER 2] Browser opened"                │
│    - WAIT 10 SECONDS                                    │
│                                                          │
│  Worker 3:                                              │
│    - Open fresh Chrome profile                          │
│    - Create DreaminaGenerator                           │
│    - Create DreaminaVideoGenerator                      │
│    - Submit login to background thread                   │
│    - Print: "[WORKER 3] Browser opened"                │
│                                                          │
└─────────────────────────────────────────────────────────┘
  │
  ▼
[STEP 3] Return workers list IMMEDIATELY (don't wait for login)
  │
  ▼
[STEP 4] Pass workers to CharacterVideoManager
  │
  ▼
Background Threads: Workers continue logging in asynchronously
```

### Timing Breakdown:
- **0s**: Worker 0 browser opens → Login starts in background
- **10s**: Worker 1 browser opens → Login starts in background
- **20s**: Worker 2 browser opens → Login starts in background
- **30s**: Worker 3 browser opens → Login starts in background
- **30s**: Function returns (all browsers open, logins running in background)

---

## Video Production Pipeline

### Phase 1: Script Generation (Sequential)
```
Duration: ~2-3 minutes
Status: ALL workers login in background during this phase

CharacterVideoManager.produce_video()
  ├─> [PHASE 1/4] SCRIPT GENERATION
  ├─> AI generates:
  │     - Story overview
  │     - Scene descriptions (4 scenes)
  │     - Character details
  │     - Dialogue
  └─> Save script.json

Background: Workers 0, 1, 2, 3 complete login
```

### Phase 2: Image Generation (Parallel)
```
Duration: ~30-60 seconds (parallel)
Workers: All 4 active

_generate_images_parallel()
  ├─> Scene 1 → Worker 0 (submit immediately)
  ├─> Scene 2 → Worker 1 (submit immediately)
  ├─> Scene 3 → Worker 2 (submit immediately)
  └─> Scene 4 → Worker 3 (submit immediately)
  
ThreadPoolExecutor: All tasks run simultaneously
Wait for all 4 images to complete
```

### Phase 3: Video Generation (Parallel)
```
Duration: ~2-5 minutes (parallel)
Workers: All 4 active

_generate_videos_parallel()
  ├─> Scene 1 → Worker 0 (use Scene 1 image as reference)
  ├─> Scene 2 → Worker 1 (use Scene 2 image as reference)
  ├─> Scene 3 → Worker 2 (use Scene 3 image as reference)
  └─> Scene 4 → Worker 3 (use Scene 4 image as reference)
  
ThreadPoolExecutor: All tasks run simultaneously
Wait for all 4 videos to complete
```

### Phase 4: Post-Production (Sequential)
```
- Thumbnail generation
- Metadata saving
- Summary generation
```

---

## Anti-Bot Features

### 1. **Staggered Browser Opening**
- 10-second delay between each browser launch
- Prevents detection of mass automation
- Total: 40 seconds to open all 4 browsers

### 2. **Fresh Chrome Profiles**
- Each worker uses `fresh_profile=True`
- Unique browser fingerprint per worker
- Separate cookies/cache/session state

### 3. **Asynchronous Login**
- Login happens naturally during script generation
- No artificial wait patterns
- Background threads simulate human multitasking

### 4. **Human-Like Delays** (in browser_utils.py)
- Random delays before typing
- Mouse movement simulation
- Natural interaction patterns

---

## Performance Comparison

### Sequential Mode (Old)
```
Script:  2-3 min
Images:  4 × 1 min  = 4 min
Videos:  4 × 3 min  = 12 min
Post:    1 min
─────────────────────────
TOTAL:   ~19-20 minutes
```

### Parallel Mode (New)
```
Workers: 40 sec (staggered opening)
Script:  2-3 min (workers login in background)
Images:  1 min (4 workers parallel)
Videos:  3 min (4 workers parallel)
Post:    1 min
──────────────────────────```
TOTAL:   ~7-8 minutes
```

**Speed Improvement: ~2.5x faster**

---

## File Structure

```
flowchart/
├── common/
│   └── shared_session.py           # SharedSessionManager
├── character/
│   ├── character_video_manager.py  # Main manager (accepts workers)
│   ├── image_generator.py          # DreaminaGenerator
│   └── video_generator.py          # DreaminaVideoGenerator
└── ...

master_manager.py                   # Implements _init_workers()
```

---

## Key Implementation Details

### master_manager.py
```python
def _init_workers(self, num_workers=4, stagger_delay=10):
    """Creates workers with staggered delays"""
    workers = []
    executor = ThreadPoolExecutor(max_workers=num_workers)
    
    for i in range(num_workers):
        # Open browser
        session = SharedSessionManager(fresh_profile=True)
        img_gen = DreaminaGenerator(shared_session=session)
        video_gen = DreaminaVideoGenerator(shared_session=session)
        
        # Start login in background (non-blocking)
        executor.submit(self._login_worker, i, session)
        
        workers.append({
            'id': i,
            'session': session,
            'img_gen': img_gen,
            'video_gen': video_gen
        })
        
        # Wait before next worker (except last)
        if i < num_workers - 1:
            time.sleep(stagger_delay)
    
    return workers  # Return immediately
```

### character_video_manager.py
```python
def _generate_images_parallel(self, scenes, project_id):
    """Parallel image generation"""
    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        for idx, scene in enumerate(scenes):
            worker = workers[idx % len(workers)]  # Round-robin
            future = executor.submit(
                worker['img_gen'].generate_image,
                prompt=prompt,
                output_path=path
            )
        # Wait for all to complete
```

---

## Usage

### Command Line:
```bash
# Sequential (1 browser)
python master_manager.py --type character --idea "Detective story" --scenes 4

# Parallel (4 browsers, 10s stagger)
python master_manager.py --type character --idea "Detective story" --scenes 4 --parallel
```

### Expected Output:
```
[MODE] Using 4-Worker Parallel Processing
[WORKERS] Initializing workers with 10s staggered delays...

[WORKER 0] Opening browser...
[WORKER 0] Browser opened, logging in background...
[STAGGER] Waiting 10s before opening Worker 1...

[WORKER 1] Opening browser...
[WORKER 1] Browser opened, logging in background...
[STAGGER] Waiting 10s before opening Worker 2...

[WORKER 2] Opening browser...
[WORKER 2] Browser opened, logging in background...
[STAGGER] Waiting 10s before opening Worker 3...

[WORKER 3] Opening browser...
[WORKER 3] Browser opened, logging in background...

[WORKERS] Launched 4/4 workers (login in progress)
[INFO] Workers will be ready by the time script generation completes

[PHASE 1/4] SCRIPT GENERATION
... (workers login in background)

[WORKER 0] ✓ Login complete
[WORKER 1] ✓ Login complete
[WORKER 2] ✓ Login complete
[WORKER 3] ✓ Login complete

[PHASE 2/4] IMAGE GENERATION
[PARALLEL] Using 4 workers for image generation
[PARALLEL] Scene 1 → Worker 0 (submitting now)
[PARALLEL] Scene 2 → Worker 1 (submitting now)
[PARALLEL] Scene 3 → Worker 2 (submitting now)
[PARALLEL] Scene 4 → Worker 3 (submitting now)
...
```

---

## Notes

1. **Workers login during script generation** - No idle time waiting for logins
2. **No stagger delays during task execution** - Workers already separated at init
3. **Round-robin task distribution** - Balanced workload across workers
4. **ThreadPoolExecutor** - Standard Python concurrency
5. **Fresh profiles per worker** - Each appears as separate user to Dreamina
