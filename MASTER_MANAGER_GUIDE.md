# Master Video Automation Manager - Quick Start

## Installation

```bash
cd "c:\Users\vijay\OneDrive\Pictures\automation tool"
pip install -r requirements.txt
```

## Usage

### 1. Single Character Video
```bash
python master_manager.py --type character --idea "Detective mystery" --scenes 5 --parallel
```

### 2. Single Info Video
```bash
python master_manager.py --type info --niche "Space discoveries" --mode ai --parallel
```

### 3. Batch Production
```bash
python master_manager.py --batch batch_config.json
```

### 4. Show Capabilities
```bash
python master_manager.py --summary
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--type` | Pipeline type | `character` or `info` |
| `--idea` | Video concept (character) | `"Detective story"` |
| `--niche` | Topic (info) | `"Ancient Egypt"` |
| `--scenes` | Number of scenes/clips | `5` |
| `--mode` | Info video mode | `ai`, `stock`, `hybrid` |
| `--parallel` | Enable parallel processing | flag |
| `--consistency` | Veo 3.1 consistency | flag (default: on) |
| `--batch` | Batch config file | `batch_config.json` |
| `--output` | Output directory | `output` |
| `--headless` | Headless browser mode | flag |
| `--summary` | Show system info | flag |

## Examples

### Character Video (Sequential)
```bash
python master_manager.py \
  --type character \
  --idea "A chef discovers ancient recipe" \
  --scenes 4
```

### Character Video (Parallel + Consistency)
```bash
python master_manager.py \
  --type character \
  --idea "Detective solves mystery" \
  --scenes 5 \
  --parallel \
  --consistency
```

### Info Video (AI-Only, Parallel)
```bash
python master_manager.py \
  --type info \
  --niche "Space exploration" \
  --mode ai \
  --scenes 6 \
  --parallel
```

### Info Video (Hybrid Mode)
```bash
python master_manager.py \
  --type info \
  --niche "Ocean wildlife" \
  --mode hybrid \
  --scenes 5
```

### Batch Production
Create `batch_config.json`:
```json
{
  "videos": [
    {
      "type": "character",
      "idea": "Detective mystery",
      "scenes": 5,
      "parallel": true
    },
    {
      "type": "info",
      "niche": "Ancient Egypt",
      "mode": "ai",
      "clips": 5,
      "parallel": true
    }
  ]
}
```

Run:
```bash
python master_manager.py --batch batch_config.json
```

## Output Structure

```
output/
├── character/           # Character videos
│   ├── scripts/
│   ├── images/
│   ├── videos/
│   └── thumbnails/
├── info/               # Info videos
│   ├── scripts/
│   ├── videos/
│   └── thumbnails/
├── logs/               # Execution logs
└── metadata/           # Production metadata
```

## Features

✅ **Character Pipeline**
- Story-based videos
- Veo 3.1 consistency
- Parallel processing (2-8x faster)
- Identity cards + Multi-reference

✅ **Info Pipeline**
- Educational videos
- AI + Stock footage
- Parallel generation (4x faster)

✅ **Automation**
- Automated scripting (LLM)
- AI media generation
- Thumbnail creation
- Batch processing

## Performance

| Mode | Processing | Speedup |
|------|------------|---------|
| Character Sequential | 1x workers | Baseline |
| Character Parallel | 2-8x workers | **4-8x faster** |
| Info Sequential | 1x workers | Baseline |
| Info Parallel | 4x workers | **4x faster** |

## Troubleshooting

**Import errors**: 
```bash
pip install selenium opencv-python requests
```

**Info pipeline not available**:
- Check `flowchart/info/` exists
- Verify imports in `info_orchestrator.py`

**Headless mode issues**:
- Remove `--headless` flag
- Check Chrome installation

## Quick Test

```bash
# Test character pipeline
python master_manager.py --type character --idea "Test video" --scenes 2

# Test info pipeline  
python master_manager.py --type info --niche "Test niche" --mode ai --scenes 2

# Show summary
python master_manager.py --summary
```
