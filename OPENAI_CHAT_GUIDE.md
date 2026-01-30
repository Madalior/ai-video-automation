# OpenAI Chat API Setup Guide

## 🔐 Security First

### ⚠️ CRITICAL ACTION REQUIRED

Your OpenAI API key was exposed when you shared it. **You must take these steps immediately:**

1. **Revoke the exposed key:**
   - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Find the key starting with `sk-proj-PPmuuQ...`
   - Click "Revoke" or delete it

2. **Create a new key:**
   - Click "Create new secret key"
   - Give it a name (e.g., "Video Automation Tool")
   - Copy the key (you'll only see it once!)

3. **Add to `.env` file:**
   - Open [`.env`](file:///c:/Users/vijay/OneDrive/Pictures/automation%20tool/.env)
   - Replace `OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE` with your **new** key
   - Save the file

---

## 📦 Installation

The required packages are already installed:
- ✅ `openai` - Official OpenAI Python library
- ✅ `python-dotenv` - Secure environment variable management

---

## 🚀 Quick Start

### 1. Set Up Your API Key

Edit `.env` and replace the placeholder:

```bash
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_NEW_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
```

### 2. Run the Example Script

```bash
python openai_chat_example.py
```

You'll see 4 options:
1. **Simple one-time chat** - Ask a single question
2. **Interactive conversation** - Multi-turn chat with memory
3. **Streaming response** - See responses in real-time
4. **Video script enhancer** - Improve your video scripts with AI

---

## 💡 Usage Examples

### Example 1: Simple Chat

```python
from openai_chat_example import simple_chat

response = simple_chat("Suggest 5 viral video niches for 2026")
print(response)
```

### Example 2: Interactive Conversation

```python
from openai_chat_example import conversational_chat

conversational_chat()
# Type your messages and it remembers context!
```

### Example 3: Enhance Video Scripts

```python
from openai_chat_example import video_script_enhancer

original_script = """
Scene 1: Introduction to AI
Scene 2: How AI works
Scene 3: Benefits of AI
"""

enhanced = video_script_enhancer(original_script)
print(enhanced)
```

---

## 🔗 Integration with Your Automation Tool

### Option A: Enhance Script Generation

Add AI-powered script enhancement to your existing `script_generator.py`:

```python
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def enhance_script_with_ai(basic_script):
    """Enhance generated scripts using OpenAI"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a viral video scriptwriter."},
            {"role": "user", "content": f"Make this script more engaging:\n\n{basic_script}"}
        ]
    )
    return response.choices[0].message.content
```

### Option B: AI-Powered Niche Discovery

Use OpenAI to find trending video niches:

```python
def discover_trending_niches():
    """Find trending video niches using AI"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a YouTube trends expert. Suggest viral video niches."
            },
            {
                "role": "user",
                "content": "What are the top 5 trending video niches for January 2026?"
            }
        ]
    )
    return response.choices[0].message.content
```

### Option C: Conversational Control Panel

Create a chat interface to control your automation pipeline:

```python
def automation_chat_assistant():
    """Chat to control video automation"""
    messages = [
        {
            "role": "system",
            "content": """You are an AI assistant that helps control a video automation tool.
            You can help users:
            - Generate video scripts
            - Choose niches
            - Create images
            - Generate videos
            - Edit and export final videos"""
        }
    ]
    
    while True:
        user_input = input("\n👤 You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        assistant_message = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_message})
        
        print(f"\n🤖 Assistant: {assistant_message}")
```

---

## 📝 Available Models

- `gpt-4` - Most capable (recommended)
- `gpt-4-turbo` - Faster, cheaper than gpt-4
- `gpt-3.5-turbo` - Fast and economical
- `gpt-4o` - Multimodal (text + images)

Change model in `.env`:
```bash
OPENAI_MODEL=gpt-4-turbo
```

---

## 💰 Pricing (as of 2026)

- **GPT-4**: ~$0.03 per 1K tokens (input), ~$0.06 per 1K tokens (output)
- **GPT-3.5-turbo**: ~$0.0015 per 1K tokens (input), ~$0.002 per 1K tokens (output)

**Tip**: Start with GPT-3.5-turbo for testing, then upgrade to GPT-4 for production.

---

## 🔧 Advanced Features

### Function Calling (Tool Use)

Let AI call your automation functions:

```python
functions = [
    {
        "name": "generate_video",
        "description": "Generate a video on a specific topic",
        "parameters": {
            "type": "object",
            "properties": {
                "niche": {"type": "string"},
                "duration": {"type": "integer"}
            },
            "required": ["niche"]
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Create a 60-second video about AI"}],
    functions=functions,
    function_call="auto"
)
```

### Vision (Analyze Images)

Use GPT-4o to analyze generated images:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Does this image match the script description?"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]
        }
    ]
)
```

---

## 🛡️ Best Practices

1. **Never expose API keys** - Always use `.env` files
2. **Use `.gitignore`** - Ensure `.env` is git-ignored (already done ✅)
3. **Rate limiting** - OpenAI has rate limits; handle errors gracefully
4. **Cost monitoring** - Check usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)
5. **Temperature control** - Lower (0.0-0.3) for factual, higher (0.7-1.0) for creative

---

## 🐛 Troubleshooting

### Error: "Invalid API Key"
- Check `.env` file has correct key
- Ensure no extra spaces or quotes
- Verify key is active on OpenAI platform

### Error: "Rate limit exceeded"
- Wait a minute and try again
- Consider upgrading your OpenAI plan
- Implement exponential backoff

### Error: "Module not found: openai"
- Run: `pip install openai python-dotenv`

---

## 📚 Next Steps

1. ✅ Set up your API key in `.env`
2. ✅ Test with `python openai_chat_example.py`
3. 🔄 Choose an integration option (A, B, or C above)
4. 🚀 Start building AI-powered features!

---

## 🔗 Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [API Key Management](https://platform.openai.com/api-keys)
- [Usage Dashboard](https://platform.openai.com/usage)
- [Pricing](https://openai.com/pricing)

---

**Ready to enhance your video automation tool with AI chat? Let me know which integration option you'd like to implement!** 🚀
