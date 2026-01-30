"""
FREE AI Assistant using your existing API keys
No rate limits! Uses Groq (fastest), Gemini, Cerebras, or SambaNova
"""

import os
import json
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# ============================================================================
# FREE AI CLIENTS (No rate limits!)
# ============================================================================

class FreeAIAssistant:
    """AI Assistant using FREE APIs - Groq, Gemini, Cerebras"""
    
    def __init__(self, provider="groq"):
        self.provider = provider
        self.client = None
        self.messages = []
        
        # Initialize based on provider
        if provider == "groq":
            self._init_groq()
        elif provider == "gemini":
            self._init_gemini()
        elif provider == "cerebras":
            self._init_cerebras()
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        # System prompt
        self.messages.append({
            "role": "system",
            "content": """You are an AI assistant controlling a video automation pipeline.

You help users:
- Generate video scripts
- Create character or info videos
- Discover trending niches
- Optimize content for retention
- Generate SEO metadata

Be helpful and conversational."""
        })
    
    def _init_groq(self):
        """Initialize Groq (FASTEST & FREE)"""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in .env")
            
            self.client = Groq(api_key=api_key)
            self.model = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
            print(f"✅ Using Groq ({self.model}) - FREE & FAST!")
        except ImportError:
            print("❌ Groq not installed. Run: pip install groq")
            raise
    
    def _init_gemini(self):
        """Initialize Google Gemini (FREE)"""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env")
            
            genai.configure(api_key=api_key)
            self.client = genai
            self.model = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
            print(f"✅ Using Google Gemini ({self.model}) - FREE!")
        except ImportError:
            print("❌ Gemini not installed. Run: pip install google-generativeai")
            raise
    
    def _init_cerebras(self):
        """Initialize Cerebras (FREE & FAST)"""
        try:
            from cerebras.cloud.sdk import Cerebras
            api_key = os.getenv("CEREBRAS_API_KEY")
            if not api_key:
                raise ValueError("CEREBRAS_API_KEY not found in .env")
            
            self.client = Cerebras(api_key=api_key)
            self.model = os.getenv("CEREBRAS_MODEL_NAME", "llama3.1-8b")
            print(f"✅ Using Cerebras ({self.model}) - FREE & FAST!")
        except ImportError:
            print("❌ Cerebras not installed. Run: pip install cerebras-cloud-sdk")
            raise
    
    def chat(self, user_message: str) -> str:
        """Send a message and get response"""
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            if self.provider == "groq":
                return self._chat_groq()
            elif self.provider == "gemini":
                return self._chat_gemini()
            elif self.provider == "cerebras":
                return self._chat_cerebras()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _chat_groq(self) -> str:
        """Chat with Groq"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply
    
    def _chat_gemini(self) -> str:
        """Chat with Gemini"""
        model = self.client.GenerativeModel(self.model)
        
        # Convert messages to Gemini format
        prompt = "\n\n".join([
            f"{m['role'].title()}: {m['content']}" 
            for m in self.messages
        ])
        
        response = model.generate_content(prompt)
        reply = response.text
        
        self.messages.append({"role": "assistant", "content": reply})
        return reply
    
    def _chat_cerebras(self) -> str:
        """Chat with Cerebras"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply
    
    def reset(self):
        """Reset conversation"""
        self.messages = self.messages[:1]  # Keep system message


# ============================================================================
# INTERACTIVE CHAT
# ============================================================================

def run_free_ai_chat():
    """Interactive chat with FREE AI"""
    print("\n" + "=" * 70)
    print("🆓 FREE AI ASSISTANT - NO RATE LIMITS!")
    print("=" * 70)
    
    print("\nChoose your FREE AI provider:")
    print("1. Groq (Llama 3.3 70B) - ⚡ FASTEST")
    print("2. Google Gemini - 🧠 SMARTEST")
    print("3. Cerebras (Llama 3.1) - ⚡ VERY FAST")
    
    choice = input("\nEnter choice (1-3, default=1): ").strip() or "1"
    
    provider_map = {
        "1": "groq",
        "2": "gemini",
        "3": "cerebras"
    }
    
    provider = provider_map.get(choice, "groq")
    
    try:
        ai = FreeAIAssistant(provider=provider)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return
    
    print("\n" + "=" * 70)
    print("Type 'quit' or 'exit' to end conversation")
    print("Type '/reset' to clear history")
    print("=" * 70)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye!")
            break
        
        if user_input.lower() == '/reset':
            ai.reset()
            print("\n🔄 Conversation reset!")
            continue
        
        response = ai.chat(user_input)
        print(f"\n🤖 Assistant: {response}")


# ============================================================================
# SIMPLE API - Direct function calls
# ============================================================================

def ask_ai(question: str, provider="groq") -> str:
    """Simple function to ask AI a question"""
    ai = FreeAIAssistant(provider=provider)
    return ai.chat(question)


def generate_video_idea(niche: str, provider="groq") -> str:
    """Generate video ideas for a niche"""
    prompt = f"Suggest 5 viral video ideas for the '{niche}' niche. Make them trending and engaging."
    return ask_ai(prompt, provider)


def improve_script(script: str, provider="groq") -> str:
    """Improve a video script"""
    prompt = f"Improve this video script to be more engaging and viral:\n\n{script}"
    return ask_ai(prompt, provider)


def discover_niches(provider="groq") -> str:
    """Discover trending niches"""
    prompt = "What are the top 5 trending video niches right now in 2026?"
    return ask_ai(prompt, provider)


# ============================================================================
# COMPARISON TEST
# ============================================================================

def test_all_providers():
    """Test all FREE providers"""
    test_question = "Suggest a viral video topic about AI in 2026"
    
    print("\n" + "=" * 70)
    print("TESTING ALL FREE AI PROVIDERS")
    print("=" * 70)
    
    providers = ["groq", "gemini", "cerebras"]
    
    for provider in providers:
        print(f"\n{'='*70}")
        print(f"Testing {provider.upper()}...")
        print(f"{'='*70}")
        
        try:
            import time
            start = time.time()
            
            response = ask_ai(test_question, provider)
            
            elapsed = time.time() - start
            
            print(f"\n⏱️  Response time: {elapsed:.2f}s")
            print(f"📝 Response:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_all_providers()
    else:
        run_free_ai_chat()
