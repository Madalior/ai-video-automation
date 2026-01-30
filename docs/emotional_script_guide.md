# Emotional Script Generation Guide

## Overview
The Emotional Script Generation system enhances all video scripts with human-like emotions, natural conversational patterns, and professional delivery guidance. It works seamlessly with both character-based and info-based video pipelines.

## Features

### 🎭 Seven Emotion Categories

1. **Joy**: Uplifting, cheerful, light-hearted energy
2. **Sadness**: Reflective, melancholic, poignant moments
3. **Excitement**: High energy, enthusiasm, anticipation
4. **Curiosity**: Engaging questions, mystery, discovery
5. **Empathy**: Understanding, relatable, compassionate
6. **Inspiration**: Motivating, uplifting, transformative
7. **Nostalgia**: Wistful, reflective, memory-driven

### 💬 Human Storytelling Patterns

- **Hook**: Opens with questions, surprising facts, or bold statements
- **Build**: Layers information progressively with mini-revelations
- **Peaks & Valleys**: Creates emotional contrast for engagement
- **Resolution**: Circles back to opening with memorable closure

### 🎤 Delivery Enhancement

- **[PAUSE]**: Strategic silence for impact
- **[EMPHASIS]**: Vocal stress on key words
- **[BUILD]**: Gradual increase in energy
- **[SOFT]**: Gentle, intimate delivery
- **Pacing hints**: Fast, moderate, slow, build, soften

## Usage

### Character Videos

```python
from flowchart.character.script_generator import ScriptGenerator

# Initialize with emotional AI (default: True)
generator = ScriptGenerator(use_emotional_ai=True)

# Generate overview
overview = generator.generate_overview("A Hero's Journey")

# Generate scenes with emotional enhancement
scenes = generator.generate_scenes(overview, num_scenes=7)

# Each scene now includes:
# - emotion: Primary emotion for the scene
# - pacing: Recommended pacing (fast/moderate/slow)
# - delivery_hint: How to deliver the dialogue
```

### Info Videos

```python
from flowchart.info.info_script_generator import InfoScriptGenerator

# Initialize with emotional AI
generator = InfoScriptGenerator(use_emotional_ai=True)

# Generate full script
script = generator.generate_full_script(
    topic="Amazing Space Facts",
    num_scenes=8,
    duration=60
)

# Each scene includes emotional metadata
for scene in script['scenes']:
    print(f"Emotion: {scene['emotion']}")
    print(f"Pacing: {scene['pacing']}")
    print(f"Delivery: {scene['delivery_hint']}")
```

### Direct Emotional Enhancement

```python
from flowchart.common.emotional_script_generator import EmotionalScriptGenerator

# Initialize
gen = EmotionalScriptGenerator(use_genkit=True)

# Enhance any script
result = gen.enhance_script(
    script="Your script text here...",
    video_type="info",  # or "character"
    emotion_style="auto",  # auto-detect or specify: joy, dramatic, educational, etc.
    num_scenes=7
)

# Access results
enhanced = result['enhanced_script']
emotion_map = result['emotion_map']
delivery_notes = result['delivery_notes']
pacing_hints = result['pacing_hints']
storytelling_arc = result['storytelling_arc']
```

## Emotion Styles

### Auto Detection
Set `emotion_style="auto"` to automatically detect the best emotion based on content keywords.

### Specific Emotions
- **"joy"**: Happy, positive content
- **"dramatic"**: Intense, emotional stories  
- **"educational"**: Info/documentary (curiosity-driven)
- **"inspirational"**: Motivational content
- **"nostalgic"**: Memory-based narratives
- **"empathetic"**: Relatable, understanding tone

## Integration with Genkit

The system uses the Genkit AI service for advanced emotional intelligence:

1. **Prompt Template**: `genkit-service/prompts/emotional_script.prompt`
2. **Endpoint**: `POST /enhance-script-emotions`
3. **Fallback**: Works offline with basic enhancement if Genkit unavailable

### Starting Genkit Service

```powershell
cd genkit-service
go run main.go
```

Service runs on `http://localhost:3400`

## Output Structure

### Enhanced Script Response

```json
{
  "enhanced_script": {
    "full_text": "Complete script with [MARKERS]",
    "scenes": [
      {
        "scene_number": 1,
        "narration": "Enhanced narration with emotion",
        "emotion": "curiosity",
        "pacing": "moderate",
        "delivery_hint": "Inquisitive tone, strategic pauses"
      }
    ]
  },
  "emotion_map": {
    "overall_arc": "Opens with hook, builds curiosity, peaks at revelation",
    "scene_emotions": ["curiosity", "excitement", "inspiration"],
    "peak_moment": "Scene 4",
    "resolution_tone": "inspiration"
  },
  "delivery_notes": [
    "Start with warm, inviting tone",
    "Build energy through scenes 2-4",
    "Use strategic pauses before revelations"
  ],
  "pacing_hints": {
    "intro": "moderate - establish connection",
    "body": "varied - mix fast facts with slower reflections",
    "conclusion": "deliberate - every word counts"
  },
  "storytelling_arc": "Journey from curiosity to understanding"
}
```

## Best Practices

### For Character Videos
- Match emotion to character's emotional state
- Use varied emotions across scenes for natural arc
- Leverage delivery hints for voice acting

### For Info Videos
- Default to "educational" or "curiosity" for learning content
- Use "inspiration" for motivational conclusions
- Mix pacing to maintain engagement

### General Tips
- **Auto mode** works well for most content
- Review delivery notes before recording narration
- Use emotion metadata to guide music selection
- Pacing hints help with video editing rhythm

## Disabling Emotional Enhancement

If needed, you can disable emotional AI:

```python
# Character script without emotion
generator = ScriptGenerator(use_emotional_ai=False)

# Info script without emotion
generator = InfoScriptGenerator(use_emotional_ai=False)
```

## Examples

### Before & After

**Original**:
```
Artificial Intelligence is changing the world.
It's being used in healthcare and education.
```

**Enhanced (Curiosity)**:
```
[PAUSE] What if I told you... [EMPHASIS]Artificial Intelligence[/EMPHASIS] 
isn't just changing the world? [PAUSE] It's revolutionizing it. 
From saving lives in healthcare [BUILD] to transforming how we learn...
```

### Emotion Markers in Action

- `[PAUSE]` → Brief silence (0.5-1 second)
- `[EMPHASIS]text[/EMPHASIS]` → Stress this word
- `[BUILD]` → Gradual increase in energy
- `[SOFT]` → Gentle, intimate tone
- `[EXCITEMENT]` → High energy burst

## Troubleshooting

### Genkit Service Not Available
The system automatically falls back to basic enhancement if Genkit service is offline.

### Import Errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Testing
Run the test files to verify functionality:
```bash
python test_emotional_character.py
python test_emotional_info.py
```

## Advanced: Custom Emotions

You can extend the system by adding custom emotions to `EmotionalScriptGenerator.EMOTION_CATEGORIES`.

---

**Ready to create human-like, emotionally engaging videos!** 🎬✨
