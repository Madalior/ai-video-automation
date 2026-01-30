"""
Multi-Model AI Orchestrator
Uses different AI models for different tasks:
- GPT-5.2: Strategic thinking, planning, complex reasoning
- Claude Sonnet 4.5: Backend code generation, Python, APIs  
- Gemini 3.0 Pro: Frontend code, UI/UX, HTML/CSS/JS
"""

import os
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class MultiModelOrchestrator:
    """Intelligent AI router that uses the best model for each task"""
    
    def __init__(self):
        self.models = {}
        self._init_models()
    
    def _init_models(self):
        """Initialize all available AI models"""
        # GPT-4o (OpenAI) - Best for thinking
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.models['gpt'] = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                print("✅ GPT-4o (Thinking AI) initialized")
            except ImportError:
                print("⚠️  Install: pip install openai")
        
        # Claude 3.5 Sonnet (Anthropic) - Best for backend
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.models['claude'] = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                print("✅ Claude 3.5 Sonnet (Backend AI) initialized")
            except ImportError:
                print("⚠️  Install: pip install anthropic")
        
        # Gemini 1.5 Pro (Google) - Best for frontend
        if os.getenv("GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.models['gemini'] = genai
                print("✅ Gemini 1.5 Pro (Frontend AI) initialized")
            except ImportError:
                print("⚠️  Install: pip install google-generativeai")
    
    def route_task(self, task_description: str) -> str:
        """Intelligently route task to best model"""
        task_lower = task_description.lower()
        
        # Frontend tasks → Gemini
        if any(word in task_lower for word in ['html', 'css', 'javascript', 'ui', 'ux', 'frontend', 'dashboard', 'webpage', 'design']):
            return 'gemini'
        
        # Backend tasks → Claude
        elif any(word in task_lower for word in ['python', 'backend', 'api', 'database', 'server', 'flask', 'django', 'fastapi']):
            return 'claude'
        
        # Strategic/thinking tasks → GPT
        elif any(word in task_lower for word in ['plan', 'strategy', 'analyze', 'think', 'reason', 'decide', 'explain']):
            return 'gpt'
        
        # Default: Use GPT for general tasks
        return 'gpt'
    
    def ask(self, prompt: str, task_type: Optional[str] = None) -> str:
        """
        Ask AI with automatic model selection
        
        Args:
            prompt: The question/task
            task_type: Force specific model ('gpt', 'claude', 'gemini') or auto-detect
        
        Returns:
            AI response
        """
        # Auto-route if not specified
        if not task_type:
            task_type = self.route_task(prompt)
        
        print(f"\n🤖 Using: {task_type.upper()}")
        
        if task_type == 'gpt':
            return self._ask_gpt(prompt)
        elif task_type == 'claude':
            return self._ask_claude(prompt)
        elif task_type == 'gemini':
            return self._ask_gemini(prompt)
        else:
            raise ValueError(f"Unknown model: {task_type}")
    
    def _ask_gpt(self, prompt: str) -> str:
        """Ask GPT-5.2 (thinking/planning)"""
        if 'gpt' not in self.models:
            return "❌ GPT not available. Add OPENAI_API_KEY to .env"
        
        response = self.models['gpt'].chat.completions.create(
            model="gpt-5.2",  # User requested model
            messages=[
                {"role": "system", "content": "You are an expert strategic thinker and planner."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def _ask_claude(self, prompt: str) -> str:
        """Ask Claude Sonnet 4.5 (backend code)"""
        if 'claude' not in self.models:
            return "❌ Claude not available. Add ANTHROPIC_API_KEY to .env"
        
        response = self.models['claude'].messages.create(
            model="claude-sonnet-4.5",  # User requested model
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _ask_gemini(self, prompt: str) -> str:
        """Ask Gemini 3.0 Pro (frontend code)"""
        if 'gemini' not in self.models:
            return "❌ Gemini not available. Add GEMINI_API_KEY to .env"
        
        model = self.models['gemini'].GenerativeModel('gemini-3.0-pro')
        response = model.generate_content(prompt)
        return response.text
    
    def collaborative_solve(self, task: str) -> Dict[str, str]:
        """
        Multi-model collaboration: All 3 AIs work together
        
        Returns:
            {
                'gpt_thinking': "Strategic plan...",
                'claude_backend': "Backend code...",
                'gemini_frontend': "Frontend code..."
            }
        """
        print(f"\n🎯 Task: {task}")
        print("=" * 70)
        
        results = {}
        
        # Step 1: GPT creates strategic plan
        print("\n1️⃣ GPT-4o: Strategic Planning...")
        plan_prompt = f"Create a strategic plan for: {task}"
        results['gpt_thinking'] = self._ask_gpt(plan_prompt)
        print(f"✅ Plan created")
        
        # Step 2: Claude writes backend
        print("\n2️⃣ Claude: Backend Development...")
        backend_prompt = f"Based on this plan, write Python backend code: {results['gpt_thinking']}"
        results['claude_backend'] = self._ask_claude(backend_prompt)
        print(f"✅ Backend code generated")
        
        # Step 3: Gemini creates frontend
        print("\n3️⃣ Gemini: Frontend Development...")
        frontend_prompt = f"Create beautiful HTML/CSS/JS frontend for: {task}"
        results['gemini_frontend'] = self._ask_gemini(frontend_prompt)
        print(f"✅ Frontend code generated")
        
        return results


# ============================================================================
# INTERACTIVE CHAT
# ============================================================================

def interactive_chat():
    """Chat with multi-model AI orchestrator"""
    print("\n" + "=" * 70)
    print("🌟 MULTI-MODEL AI ORCHESTRATOR")
    print("=" * 70)
    print("Specialized AI Team:")
    print("  🧠 GPT-5.2           → Strategic thinking, planning, analysis")
    print("  🐍 Claude Sonnet 4.5 → Backend code (Python, APIs, databases)")
    print("  🎨 Gemini 3.0 Pro    → Frontend code (HTML, CSS, JavaScript)")
    print("\nCommands:")
    print("  /gpt <prompt>     - Force GPT")
    print("  /claude <prompt>  - Force Claude")
    print("  /gemini <prompt>  - Force Gemini")
    print("  /collab <task>    - All 3 AIs collaborate")
    print("  quit              - Exit")
    print("=" * 70)
    
    orchestrator = MultiModelOrchestrator()
    
    if not orchestrator.models:
        print("\n❌ No AI models available!")
        print("Add at least one API key to .env:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        return
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye!")
            break
        
        try:
            # Handle commands
            if user_input.startswith('/gpt '):
                response = orchestrator.ask(user_input[5:], 'gpt')
                print(f"\n🧠 GPT: {response}")
            
            elif user_input.startswith('/claude '):
                response = orchestrator.ask(user_input[8:], 'claude')
                print(f"\n🐍 Claude: {response}")
            
            elif user_input.startswith('/gemini '):
                response = orchestrator.ask(user_input[8:], 'gemini')
                print(f"\n🎨 Gemini: {response}")
            
            elif user_input.startswith('/collab '):
                results = orchestrator.collaborative_solve(user_input[8:])
                print("\n" + "=" * 70)
                print("📊 COLLABORATION RESULTS")
                print("=" * 70)
                for key, value in results.items():
                    print(f"\n### {key.upper()}")
                    print(value[:500] + "..." if len(value) > 500 else value)
            
            else:
                # Auto-route
                response = orchestrator.ask(user_input)
                print(f"\n🤖 Response: {response}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    interactive_chat()
