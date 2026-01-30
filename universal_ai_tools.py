"""
Multi-Model AI Tools Integration
Supports Anthropic Claude and Google Gemini
"""

import os
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# MULTI-MODEL CLIENT MANAGER
# ============================================================================

class MultiModelClient:
    """Unified interface for multiple AI providers (Claude, Gemini)"""
    
    def __init__(self):
        self.anthropic_client = None
        self.gemini_client = None
        
        # Initialize available clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize all available AI clients"""
        # Anthropic Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                print("✅ Anthropic (Claude) client initialized")
            except ImportError:
                print("⚠️  Anthropic library not installed: pip install anthropic")
        
        # Google Gemini
        if os.getenv("GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.gemini_client = genai
                print("✅ Google Gemini client initialized")
            except ImportError:
                print("⚠️  Google Gemini library not installed: pip install google-generativeai")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        
        if self.anthropic_client:
            models.extend([
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022",
                "claude-sonnet-4.5"
            ])
        
        if self.gemini_client:
            models.extend([
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-3.0-pro"
            ])
        
        return models
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Any:
        """Unified chat interface for all models"""
        
        # Determine provider from model name
        if model.startswith("claude"):
            return self._chat_anthropic(model, messages, tools, **kwargs)
        elif model.startswith("gemini"):
            return self._chat_gemini(model, messages, tools, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model}. Available: claude-*, gemini-*")
    
    def _chat_anthropic(self, model: str, messages: List, tools: Optional[List] = None, **kwargs):
        """Anthropic Claude chat"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Check API key.")
        
        # Convert messages format (Claude uses different format)
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]
        
        params = {
            "model": model,
            "messages": user_messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        
        if system_msg:
            params["system"] = system_msg
        
        if tools:
            # Convert tool format to Claude format
            params["tools"] = self._convert_tools_to_claude(tools)
        
        return self.anthropic_client.messages.create(**params)
    
    def _chat_gemini(self, model: str, messages: List, tools: Optional[List] = None, **kwargs):
        """Google Gemini chat"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized. Check API key.")
        
        # Create model instance
        gemini_model = self.gemini_client.GenerativeModel(model)
        
        # Convert messages to Gemini format
        prompt = self._convert_messages_to_gemini(messages)
        
        # Generate response
        response = gemini_model.generate_content(prompt)
        return response
    
    def _convert_tools_to_claude(self, tools: List[Dict]) -> List[Dict]:
        """Convert tool format to Claude format"""
        claude_tools = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                claude_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
        return claude_tools
    
    def _convert_messages_to_gemini(self, messages: List[Dict]) -> str:
        """Convert message history to Gemini prompt format"""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)


# ============================================================================
# ENHANCED AUTOMATION AI WITH MULTI-MODEL SUPPORT
# ============================================================================

class UniversalAutomationAI:
    """Multi-model conversational AI for automation control"""
    
    def __init__(self, model: str = None):
        self.client = MultiModelClient()
        self.available_models = self.client.get_available_models()
        
        # Default model selection
        if model and model in self.available_models:
            self.model = model
        elif "claude-3-5-sonnet-20241022" in self.available_models:
            self.model = "claude-3-5-sonnet-20241022"
        elif "gemini-2.0-flash-exp" in self.available_models:
            self.model = "gemini-2.0-flash-exp"
        elif self.available_models:
            self.model = self.available_models[0]
        else:
            raise ValueError("No AI models available! Please configure API keys.")
        
        print(f"\n🤖 Using model: {self.model}")
        print(f"📋 Available models: {', '.join(self.available_models)}")
        
        # Message history
        self.messages = [
            {
                "role": "system",
                "content": """You are an AI assistant controlling a video automation pipeline.

Available commands:
- generate_video_script: Create scripts
- create_character_video: Character-based videos
- create_info_video: Info videos with stock/AI
- discover_trending_niches: Find trending topics
- batch_produce_videos: Mass production
- check_pipeline_status: Status checks
- optimize_for_retention: Retention optimization
- generate_metadata: SEO metadata

Be helpful, conversational, and proactive."""
            }
        ]
    
    def switch_model(self, new_model: str):
        """Switch to a different AI model"""
        if new_model not in self.available_models:
            return f"Model '{new_model}' not available. Choose from: {', '.join(self.available_models)}"
        
        self.model = new_model
        return f"Switched to {new_model}"
    
    def chat(self, user_message: str, use_tools: bool = True) -> str:
        """Send message and get response"""
        from openai_tools_automation import TOOLS, execute_function
        
        # Add user message
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            # Get response based on model type
            if self.model.startswith("claude"):
                return self._chat_with_claude(use_tools, TOOLS, execute_function)
            elif self.model.startswith("gemini"):
                return self._chat_with_gemini()
            else:
                return "Unsupported model"
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n❌ {error_msg}")
            return error_msg
    
    def _chat_with_claude(self, use_tools: bool, TOOLS, execute_function) -> str:
        """Chat using Claude models"""
        # Claude implementation would go here
        # For now, return simple response
        response = self.client.chat(
            model=self.model,
            messages=[m for m in self.messages if m["role"] != "system"],
            max_tokens=4096
        )
        
        content = response.content[0].text
        self.messages.append({"role": "assistant", "content": content})
        return content
    
    def _chat_with_gemini(self) -> str:
        """Chat using Gemini models"""
        response = self.client.chat(
            model=self.model,
            messages=self.messages
        )
        
        content = response.text
        self.messages.append({"role": "assistant", "content": content})
        return content
    
    def reset(self):
        """Reset conversation"""
        self.messages = self.messages[:1]


# ============================================================================
# INTERACTIVE INTERFACE
# ============================================================================

def run_universal_chat():
    """Interactive chat with model selection"""
    print("\n" + "=" * 70)
    print("🌐 UNIVERSAL AI AUTOMATION ASSISTANT")
    print("=" * 70)
    
    try:
        ai = UniversalAutomationAI()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\nPlease configure at least one API key in .env:")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        return
    
    print("\nCommands:")
    print("  /models        - List available models")
    print("  /switch MODEL  - Switch AI model")
    print("  /reset         - Clear conversation")
    print("  quit/exit      - Exit")
    print("=" * 70)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye!")
            break
        
        if user_input.lower() == '/models':
            print(f"\n📋 Available models:")
            for model in ai.available_models:
                marker = "✓" if model == ai.model else " "
                print(f"  [{marker}] {model}")
            continue
        
        if user_input.lower().startswith('/switch '):
            new_model = user_input[8:].strip()
            result = ai.switch_model(new_model)
            print(f"\n{result}")
            continue
        
        if user_input.lower() == '/reset':
            ai.reset()
            print("\n🔄 Conversation reset!")
            continue
        
        # Regular chat
        response = ai.chat(user_input)
        print(f"\n🤖 Assistant: {response}")


if __name__ == "__main__":
    run_universal_chat()
