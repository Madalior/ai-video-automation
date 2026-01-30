# Multi-Model AI Orchestrator - Quick Start

## 🎯 What This Does

Uses **3 specialized AI models** for different tasks:

| AI Model | Best For | Example |
|----------|----------|---------|
| **GPT-4o (Latest)** | 🧠 Strategic thinking, planning | "Plan a video automation system" |
| **Claude 3.5 Sonnet** | 🐍 Backend code (Python) | "Write a Flask API for video processing" |
| **Gemini 1.5 Pro** | 🎨 Frontend code (HTML/CSS/JS) | "Create a beautiful dashboard UI" |

---

## 🚀 Usage

### **Run It:**
```bash
python multi_model_orchestrator.py
```

### **Commands:**

**Auto-routing** (AI picks best model):
```
You: Create a dashboard for video automation
→ Automatically uses Gemini for frontend
```

**Force specific model:**
```
/gpt How should I architect my system?
/claude Write Python code for video processing
/gemini Design a modern UI
```

**Collaborative mode** (all 3 AIs work together):
```
/collab Build a video automation dashboard
→ GPT plans strategy
→ Claude writes backend
→ Gemini creates frontend
```

---

## ⚙️ Setup

### **Required API Keys:**

Add to `.env`:
```bash
# GPT-4o (already configured)
OPENAI_API_KEY=your_key_here

# Claude 3.5 Sonnet (get from anthropic.com)
ANTHROPIC_API_KEY=your_claude_key

# Gemini 1.5 Pro (already configured)
GEMINI_API_KEY=AIzaSy...
```

### **Install Libraries:**
```bash
pip install openai anthropic google-generativeai
```

---

## 💡 Example Workflow

```
👤 /gpt Plan a video automation system

🧠 GPT: Here's the strategic approach:
   1. Modular architecture
   2. Separate frontend/backend
   3. API-driven design...

👤 /claude Implement the backend based on that plan

🐍 Claude: *generates Python Flask backend code*

👤 /gemini Create the frontend dashboard

🎨 Gemini: *generates beautiful HTML/CSS/JS*
```

---

## ✨ Benefits

- ✅ Best model for each task
- ✅ No Antigravity rate limits
- ✅ Run 24/7 on your computer
- ✅ Full control over prompts
- ✅ Cost-effective (pay only for what you use)

**Ready to use!** 🚀
