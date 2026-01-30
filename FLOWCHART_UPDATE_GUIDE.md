# Flowchart Update - Missing Components

## Current Status
The FLOWCHART.drawio is a Draw.io XML file showing the video automation pipeline split into **Character** (left) and **Info** (right) branches.

## ✅ Already Included in Flowchart
- Character pipeline (script → image → video → edit → upload)
- Info pipeline (script → image → video → voiceover → edit → upload)
- Core tools note at bottom
- Retention optimizer
- AI metadata generator
- Smart uploader

## ❌ Missing - New Veo 3.1 Consistency Components

### 1. **Master Manager** (Top Level)
**File**: `master_manager.py`  
**Location**: Should be added at the very top, before the Character/Info split  
**Description**: "Master Orchestrator" box that feeds into the choice diamond

### 2. **Common Utilities Layer** (Middle Section)
**Files in `flowchart/common/`**:

#### Veo 3.1 Consistency Tools (NEW)
- `identity_cards.py` - Character identity management
- `prompt_builder.py` - Anchor/delta prompt construction  
- `frame_extractor.py` - Extract frames from videos
- `frame_controller.py` - Scene transition control

#### Existing Common Tools
- `llm_manager.py` ✅ (already shown in core tools note)
- `browser_utils.py` - Browser automation utilities
- `stock_media.py` ✅ (already shown in core tools note)

### 3. **Enhanced Script Generator** (Character Pipeline)
**File**: `enhanced_script_generator.py`  
**Location**: Should replace or complement `script_generator.py` in character branch  
**Description**: "Enhanced Script Generator (with Identity Cards)"

### 4. **Parallel Processing Indicators**
**Files**:
- `parallel_info_director.py` (info pipeline)
- `character_orchestrator.py` (character pipeline)

**Location**: Add annotations showing "Parallel Mode Available (4-8x faster)"

---

## Recommended Flowchart Updates

### Update 1: Add Master Manager at Top
```
[Gmail Uploader] (existing)
         ↓
[MASTER MANAGER] (NEW)
  @master_manager.py
  - Unified CLI
  - Batch processing
  - Both pipelines
         ↓
[Choose: Character/Info] (existing diamond)
```

### Update 2: Add Veo 3.1 Consistency Layer
Add a new layer in the **Character Pipeline** between Script and Image:

```
[Script Generator]
         ↓
[CONSISTENCY LAYER] (NEW - highlight box)
├─ Identity Cards (@identity_cards.py)
├─ Prompt Builder (@prompt_builder.py) 
├─ Frame Controller (@frame_controller.py)
└─ Frame Extractor (@frame_extractor.py)
         ↓
[Image Generator]
         ↓
[Video Generator]
   (now uses multi-reference)
```

### Update 3: Update Character Script Generator
Replace:
```
[Script generation
 @script_generator.py]
```

With:
```
[Enhanced Script Generator
 @enhanced_script_generator.py
 (creates identity cards)]
```

### Update 4: Update Video Generator Box
Replace:
```
[video generation
 @video_generator.py
 (AI only, with character)]
```

With:
```
[video generation
 @video_generator.py
 (Multi-reference: up to 3 images)
 (Veo 3.1 consistency: 95%+)]
```

### Update 5: Add Parallel Processing Note
Add colored badges next to:
- **Character Orchestrator**: "⚡ Parallel: 4-8x faster"
- **Parallel Info Director**: "⚡ Parallel: 4x faster"

### Update 6: Update Core Tools Box at Bottom
Replace:
```
CORE TOOLS (used throughout):
@llm_manager.py (Gemini AI)
@stock_media.py (Pexels/Pixabay)
```

With:
```
CORE TOOLS (used throughout):
@llm_manager.py (Gemini AI)
@stock_media.py (Pexels/Pixabay)
@browser_utils.py (Automation)

VOO 3.1 CONSISTENCY TOOLS:
@identity_cards.py (Character anchors)
@prompt_builder.py (Anchor/delta prompts)
@frame_controller.py (Scene transitions)
@frame extractor.py (Frame extraction)
```

---

## Visual Additions Needed

### Box Colors
- **NEW Master Manager**: Orange (#FFE6CC)
- **Veo 3.1 Consistency Layer**: Light Purple (#E1D5E7)
- **Enhanced components**: Add star ⭐ icon

### Annotations
- Add version badge: "v1.0 - Veo 3.1 Integrated"
- Add legend showing new vs existing components

---

## Complete File List by Location

### Root Level
- ✅ master_manager.py (ADD TO FLOWCHART)
- ✅ batch_config.json

### flowchart/common/
- ✅ llm_manager.py (shown in core tools)
- ✅ stock_media.py (shown in core tools)
- ✅ browser_utils.py (ADD TO FLOWCHART)
- ⭐ identity_cards.py (ADD TO FLOWCHART - NEW)
- ⭐ prompt_builder.py (ADD TO FLOWCHART - NEW)
- ⭐ frame_extractor.py (ADD TO FLOWCHART - NEW)
- ⭐ frame_controller.py (ADD TO FLOWCHART - NEW)
- retention_optimizer.py (already shown)
- retention_predictor.py (already shown)
- ai_metadata_generator.py (already shown)
- smart_uploader.py (already shown)

### flowchart/character/
- ✅ script_generator.py (shown)
- ⭐ enhanced_script_generator.py (ADD TO FLOWCHART - NEW)
- ✅ image_generator.py (shown)
- ✅ video_generator.py (shown - needs update for multi-ref)
- ✅ character_orchestrator.py (ADD PARALLEL BADGE)
- ✅ character_video_manager.py

### flowchart/info/
- ✅ info_script_generator.py (shown)
- ✅ info_image_generator.py (shown)
- ✅ hybrid_info_video_generator.py (shown)
- ✅ parallel_info_director.py (ADD PARALLEL BADGE)

---

## Implementation Steps

1. **Open FLOWCHART.drawio** in Draw.io
2. **Add Master Manager** box at top (orange)
3. **Insert Veo 3.1 Consistency Layer** (purple box) in character pipeline
4. **Update script_generator** to enhanced_script_generator
5. **Update video_generator** description to mention multi-reference
6. **Add parallel processing badges** to both orchestrators
7. **Expand Core Tools box** to include Veo 3.1 modules
8. **Add legend** showing new vs existing (⭐ = new)
9. **Save and commit** to GitHub

---

**Summary**: The flowchart needs **8 major additions** to reflect the new Veo 3.1 consistency architecture and master manager integration!
