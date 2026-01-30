# OpenAI Tools & Function Calling Guide

## 🎯 Overview

You now have a powerful **conversational AI system** that can control your entire video automation pipeline through natural language!

---

## 📁 Files Created

1. **[`openai_tools_automation.py`](file:///c:/Users/vijay/OneDrive/Pictures/automation%20tool/openai_tools_automation.py)** - OpenAI function calling with 8 automation tools
2. **[`universal_ai_tools.py`](file:///c:/Users/vijay/OneDrive/Pictures/automation%20tool/universal_ai_tools.py)** - Multi-model support (GPT, Claude, Gemini)
3. **[`openai_chat_example.py`](file:///c:/Users/vijay/OneDrive/Pictures/automation%20tool/openai_chat_example.py)** - Basic chat examples

---

## 🔧 Available Tools (Functions)

Your AI assistant can execute these 8 automation tools:

### 1. **generate_video_script**
Generate video scripts for any niche

**Example:**
```
You: Create a script about AI technology trends
AI: *generates script with 7 scenes, 56 seconds*
```

### 2. **create_character_video**
Create character-based videos with AI

**Example:**
```
You: Create a character video about a tech reviewer named Sarah
AI: *starts character video production*
```

### 3. **create_info_video**
Create info videos with stock or AI footage

**Example:**
```
You: Make an info video about health tips using stock footage
AI: *starts info video pipeline*
```

### 4. **discover_trending_niches**
Find trending video topics

**Example:**
```
You: What niches are trending right now?
AI: *analyzes trends and suggests niches*
```

### 5. **batch_produce_videos**
Mass produce multiple videos

**Example:**
```
You: Create 10 character videos in parallel mode
AI: *starts batch production with 8x speedup*
```

### 6. **check_pipeline_status**
Check automation pipeline status

**Example:**
```
You: What's the status of my videos?
AI: *shows active/completed videos*
```

### 7. **optimize_for_retention**
Optimize videos for viewer retention

**Example:**
```
You: Optimize my latest video for retention
AI: *analyzes and suggests improvements*
```

### 8. **generate_metadata**
Create SEO-optimized metadata

**Example:**
```
You: Generate metadata for my AI video
AI: *creates title, description, tags*
```

---

## 🚀 Quick Start

### Option 1: OpenAI Only (Recommended)

```bash
python openai_tools_automation.py
```

**Features:**
- ✅ Full function calling support
- ✅ All 8 automation tools
- ✅ Best tool execution
- 💰 Requires OpenAI API key

### Option 2: Multi-Model (GPT, Claude, Gemini)

```bash
python universal_ai_tools.py
```

**Features:**
- ✅ Multiple AI providers
- ✅ Switch models on-the-fly
- ✅ Fallback options
- 💰 Requires at least one API key

### Option 3: Simple Examples

```bash
python openai_chat_example.py
```

**Features:**
- ✅ Basic chat functionality
- ✅ Script enhancement
- ✅ No function calling
- 💰 OpenAI only

---

## 💬 Example Conversations

### Example 1: Generate a Video

```
👤 You: I want to create a video about productivity hacks

🤖 Assistant: Great! Let me help you with that. What type of video would you like?
1. Character-based (with an AI presenter)
2. Info video (stock footage or AI-generated)

👤 You: Info video with AI-generated clips

🔧 Executing: create_info_video
Arguments: {
  "niche": "productivity",
  "video_type": "ai"
}

🤖 Assistant: Perfect! I've started creating an AI-generated info video about 
productivity hacks. This will take approximately 30-60 minutes (or 5-10 minutes 
with parallel mode). The video will include multiple scenes with AI-generated 
visuals. Would you like me to also generate SEO metadata for it?
```

### Example 2: Batch Production

```
👤 You: Create 5 videos about different tech topics using parallel processing

🔧 Executing: batch_produce_videos
Arguments: {
  "num_videos": 5,
  "pipeline_type": "info",
  "use_parallel": true
}

🤖 Assistant: Excellent! I've queued 5 tech videos for batch production with 
parallel processing enabled (8x faster). Estimated completion time: 18-19 minutes 
instead of 2.5 hours. The system will use 8 Chrome instances simultaneously.
```

### Example 3: Niche Discovery + Script + Video

```
👤 You: Find me a trending niche and create a video about it

🔧 Executing: discover_trending_niches
Arguments: {"method": "auto"}

🤖 Assistant: I found these trending niches:
1. AI & Technology
2. Personal Finance
3. Health & Wellness

Which one interests you?

👤 You: AI & Technology

🔧 Executing: generate_video_script
Arguments: {
  "niche": "AI & Technology",
  "topic": "Latest AI Breakthroughs 2026"
}

🔧 Executing: create_info_video
Arguments: {
  "niche": "AI & Technology",
  "video_type": "hybrid"
}

🤖 Assistant: Perfect! I've created a script about "Latest AI Breakthroughs 2026" 
and started video production using a hybrid approach (mix of AI and stock footage). 
The video will be ready soon!
```

---

## 🎮 Interactive Commands

When running the AI tools, you can use these commands:

### In `universal_ai_tools.py`:

- `/models` - List all available AI models
- `/switch MODEL` - Switch to a different model
  ```
  /switch gpt-4-turbo
  /switch claude-3-5-sonnet-20241022
  /switch gemini-2.0-flash-exp
  ```
- `/reset` - Clear conversation history
- `quit` or `exit` - Exit the program

---

## 🤖 Supported AI Models

### OpenAI GPT
- `gpt-4` - Most capable
- `gpt-4-turbo` - Faster, cheaper
- `gpt-4o` - Multimodal
- `gpt-3.5-turbo` - Economical

### Anthropic Claude
- `claude-3-5-sonnet-20241022` - Latest, best
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fast

### Google Gemini
- `gemini-2.0-flash-exp` - Latest experimental
- `gemini-1.5-pro` - Most capable
- `gemini-1.5-flash` - Fast

---

## ⚙️ Configuration

### Setup API Keys in `.env`

```bash
# OpenAI (Required for function calling)
OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Anthropic Claude (Optional)
ANTHROPIC_API_KEY=your_claude_key

# Already configured:
GEMINI_API_KEY=AIzaSyApIK1dhfNja6FefXXMS_OBzDQtavHe8LA
```

### Install Dependencies

```bash
# Core (already installed)
pip install openai python-dotenv

# Optional: For multi-model support
pip install anthropic google-generativeai
```

---

## 🔗 Integration with Existing Pipeline

### Connect to Real Automation

To connect the AI tools to your actual pipeline, update the execution functions in [`openai_tools_automation.py`](file:///c:/Users/vijay/OneDrive/Pictures/automation%20tool/openai_tools_automation.py):

#### Example: Real Script Generation

```python
def execute_generate_video_script(niche, topic, duration=56, num_scenes=7):
    """Execute REAL video script generation"""
    from pipelines.character.script_generator import ScriptGenerator
    
    generator = ScriptGenerator()
    script = generator.generate_script(
        niche=niche,
        topic=topic,
        duration=duration,
        num_scenes=num_scenes
    )
    
    return {
        "status": "success",
        "script_path": script.output_path,
        "scenes": len(script.scenes)
    }
```

#### Example: Real Video Production

```python
def execute_create_character_video(character_name, character_description, script_file=None):
    """Execute REAL character video production"""
    from master_manager import VideoProducer
    
    producer = VideoProducer(pipeline_type="character")
    result = producer.produce_video(
        niche="custom",
        character_name=character_name,
        character_desc=character_description
    )
    
    return {
        "status": "success",
        "video_path": result.final_video,
        "duration": result.duration
    }
```

---

## 🎯 Use Cases

### 1. **Quick Video Production**
```
"Create a 60-second video about crypto trends"
```

### 2. **Batch Automation**
```
"Make 10 videos about different health topics in parallel"
```

### 3. **Content Planning**
```
"Find 5 trending niches and create a video for each"
```

### 4. **Optimization Workflow**
```
"Generate a video, optimize it for retention, and create SEO metadata"
```

### 5. **A/B Testing**
```
"Create two versions of the same video with different styles"
```

---

## 🛡️ Security Reminders

> [!CAUTION]
> **CRITICAL:** Your OpenAI API key was exposed earlier. Please:
> 1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
> 2. Revoke the key starting with `sk-proj-PPmuuQ...`
> 3. Create a NEW key
> 4. Update `.env` file

### Best Practices:
- ✅ Never commit `.env` to git (already configured)
- ✅ Use environment variables only
- ✅ Rotate keys periodically
- ✅ Monitor usage at [OpenAI Dashboard](https://platform.openai.com/usage)

---

## 🐛 Troubleshooting

### Error: "Invalid API Key"
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Make sure there are no extra spaces or quotes
OPENAI_API_KEY=sk-proj-actualkey  # ✅ Correct
OPENAI_API_KEY="sk-proj-actualkey" # ❌ Wrong (remove quotes)
```

### Error: "Module not found: anthropic"
```bash
pip install anthropic
```

### Error: "No function execution"
Make sure you're using `openai_tools_automation.py`, not the basic examples.

### Tools not working properly
- Only GPT-4 and GPT-3.5-turbo support function calling reliably
- Claude and Gemini have limited tool support (use GPT for best results)

---

## 📚 Additional Resources

- [OpenAI Function Calling Docs](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Cookbook](https://cookbook.openai.com/)
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [Google Gemini Docs](https://ai.google.dev/docs)

---

## 🎉 Next Steps

1. ✅ Set up your OpenAI API key (IMPORTANT!)
2. ✅ Test with: `python openai_tools_automation.py`
3. 🔄 Try natural language commands
4. 🚀 Connect to real automation pipeline
5. 💡 Create custom tools for your workflow

**Start chatting with your automation system now!** 🤖
