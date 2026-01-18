# Parallel Workers Location Guide

## Image Generator - Parallel Workers

### Location
📁 **File**: `flowchart/character/image_generator.py`  
📍 **Lines**: 739-877

### Class: `MultiDreaminaGenerator`

**Purpose**: Manages multiple Chrome instances for parallel image generation

**Key Features**:
- **Workers**: Default 2, configurable up to 8+
- **Chrome Profiles**: Separate profile per worker (`chrome_data_img_0`, `chrome_data_img_1`, etc.)
- **Staggered Launch**: 10-second delays between workers
- **ThreadPoolExecutor**: Uses Python's concurrent.futures

**Usage**:
```python
from flowchart.character.image_generator import MultiDreaminaGenerator

# Initialize with 4 workers
multi_gen = MultiDreaminaGenerator(num_workers=4, headless=False)

# Batch generate images
tasks = [
    {'prompt': 'Character 1', 'output_path': 'output/char1.png'},
    {'prompt': 'Character 2', 'output_path': 'output/char2.png'},
    {'prompt': 'Character 3', 'output_path': 'output/char3.png'},
    {'prompt': 'Character 4', 'output_path': 'output/char4.png'},
]

results = multi_gen.generate_batch(tasks)
# Processes all 4 images simultaneously!
```

**Worker Architecture**:
```
MultiDreaminaGenerator
├── Worker 0 (chrome_data_img_0) → Image 1
├── Worker 1 (chrome_data_img_1) → Image 2  
├── Worker 2 (chrome_data_img_2) → Image 3
└── Worker 3 (chrome_data_img_3) → Image 4
   ↓ All execute in parallel
   Results aggregated
```

---

## Video Generator - Parallel Workers

### Location
📁 **File**: `flowchart/character/video_generator.py`  
📍 **Lines**: NOT YET IMPLEMENTED

### Status: ⚠️ **Missing Parallel Implementation**

**Current**: Only single-worker `DreaminaVideoGenerator` exists  
**Expected**: `MultiVeo3Generator` or similar class (referenced in memory but not implemented)

**What's Missing**:
```python
# This class DOES NOT EXIST yet:
class MultiVeo3Generator:
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
    
    def generate_batch(self, tasks):
        # Should work like MultiDreaminaGenerator
        # but for video generation
        pass
```

---

## Where Character Orchestrator Uses Parallel Workers

### Location
📁 **File**: `flowchart/character/character_orchestrator.py`  
📍 **Lines**: 231-393 (Image), 397-565 (Video)

### Current Implementation

**Image Generation** (Lines 231-245):
```python
# Uses MultiDreaminaGenerator for parallel image generation
from modules.generators.image_generator import MultiDreaminaGenerator

multi_img_gen = MultiDreaminaGenerator(num_workers=self.num_image_workers)
image_paths = multi_img_gen.generate_batch(image_tasks)
```

**Video Generation** (Lines 397-445):
```python
# Video is SEQUENTIAL - processes one at a time!
# No parallel implementation currently active
for scene in scenes:
    gen.generate_video(prompt, reference_image, output_path)
    # ↑ This runs serially, waiting for each to complete
```

---

## How to Enable Parallel Video Generation

### Option 1: Use Character Orchestrator (Already Has Parallel!)

Actually, the `character_orchestrator.py` DOES implement parallel video generation!

📁 **File**: `flowchart/character/character_orchestrator.py`  
📍 **Method**: `step_5_video_generation()` (Lines 397-565)

**It uses**:
```python
# Parallel video generation with ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=self.num_video_workers) as executor:
    for task in tasks:
        future = executor.submit(
            self._generate_single_video,
            worker_id,
            prompt,
            reference_images,
            output_path
        )
```

**Workers**: 4 separate Veo3Generator instances
- `chrome_data_video_0` through `chrome_data_video_3`
- Each processes scenes in parallel

### Option 2: Create MultiVeo3Generator Class

Following the `MultiDreaminaGenerator` pattern, create:

📁 **File**: `modules/generators/video_generator.py`  
📝 **Add**: `MultiVeo3Generator` class (Lines 800+)

```python
class MultiVeo3Generator:
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
    
    def generate_batch(self, tasks):
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Similar to MultiDreaminaGenerator logic
            pass
```

---

## Summary

| Component | Parallel Implementation | Location | Status |
|-----------|------------------------|----------|--------|
| **Image Generator** | `MultiDreaminaGenerator` | `flowchart/character/image_generator.py:739` | ✅ **Working** |
| **Video Generator** | `MultiVeo3Generator` | NOT IMPLEMENTED | ❌ **Missing** |
| **Character Orchestrator** | ThreadPoolExecutor | `flowchart/character/character_orchestrator.py:397` | ✅ **Working** |
| **Info Pipeline** | `ParallelInfoDirector` | `flowchart/info/parallel_info_director.py` | ✅ **Working** |

---

## Speedup Comparison

**Without Parallel** (Sequential):
- 4 images: ~8 minutes (2 min each)
- 4 videos: ~16 minutes (4 min each)
- **Total**: 24 minutes

**With Parallel** (4 workers):
- 4 images: ~2 minutes (all at once)
- 4 videos: ~4 minutes (all at once)
- **Total**: 6 minutes
- **Speedup**: **4x faster** 🚀
