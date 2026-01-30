import os
import json
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    """
    Manages multiple LLM providers with automatic failover.
    Primary: Groq (FREE & Fast), Backups: Gemini, GitHub, SambaNova, Cerebras.
    """
    def __init__(self):
        self.providers = [
            self._call_groq,          # Primary: FREE & Fast (Llama 3)
            self._call_gemini,        # Backup: Gemini 2.0
            self._call_github,        # Backup: GPT-4o via GitHub
            self._call_sambanova,     # Backup: Llama 3.1
            self._call_cerebras,      # Backup: Fast inference
        ]
        
        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # gemini-1.5-flash is deprecated, using 2.0-flash
            self.gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash"))

    # ... (other code)

    def _call_sambanova(self, prompt, json_mode):
        key = os.getenv("SAMBANOVA_API_KEY")
        if not key: raise Exception("No API Key")
        
        client = OpenAI(base_url="https://api.sambanova.ai/v1", api_key=key)
        # Using updated model name
        return self._openai_chat(client, os.getenv("SAMBANOVA_MODEL_NAME", "Meta-Llama-3.1-8B-Instruct"), prompt, json_mode)

    def generate(self, prompt, json_mode=True):
        """
        Try providers strictly in order until one succeeds.
        """
        for provider in self.providers:
            try:
                print(f"[INFO] LLM Manager: Trying {provider.__name__.replace('_call_', '').upper()}...")
                result = provider(prompt, json_mode)
                if result:
                    print(f"[SUCCESS] Success with {provider.__name__.replace('_call_', '').upper()}")
                    return result
            except Exception as e:
                print(f"[WARNING] {provider.__name__.replace('_call_', '').upper()} Failed: {str(e)[:100]}...")
                continue
        
        print("[ERROR] All LLM providers failed.")
        return None

    
    # --- PROVIDERS ---

    def _call_gemini(self, prompt, json_mode):
        if not os.getenv("GEMINI_API_KEY"): raise Exception("No API Key")
        
        config = {"response_mime_type": "application/json"} if json_mode else {}
        response = self.gemini_model.generate_content(prompt, generation_config=config)
        content = response.text
        if json_mode:
             # Clean up markdown code blocks if present
            clean_content = content.strip()
            if clean_content.startswith("```"):
                clean_content = clean_content.split("\n", 1)[1]
                if clean_content.endswith("```"):
                    clean_content = clean_content.rsplit("\n", 1)[0]
            clean_content = clean_content.strip()
            return json.loads(clean_content)
        return content

    def _call_groq(self, prompt, json_mode):
        key = os.getenv("GROQ_API_KEY")
        if not key: raise Exception("No API Key")
        
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
        return self._openai_chat(client, os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192"), prompt, json_mode)

    def _call_cerebras(self, prompt, json_mode):
        key = os.getenv("CEREBRAS_API_KEY")
        if not key: raise Exception("No API Key")
        
        client = OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)
        return self._openai_chat(client, os.getenv("CEREBRAS_MODEL_NAME", "llama3-8b-8192"), prompt, json_mode)

    def _call_sambanova(self, prompt, json_mode):
        key = os.getenv("SAMBANOVA_API_KEY")
        if not key: raise Exception("No API Key")
        
        client = OpenAI(base_url="https://api.sambanova.ai/v1", api_key=key)
        return self._openai_chat(client, os.getenv("SAMBANOVA_MODEL_NAME", "Meta-Llama-3.1-8B-Instruct"), prompt, json_mode)

    def _call_github(self, prompt, json_mode):
        key = os.getenv("GITHUB_TOKEN")
        if not key: raise Exception("No API Key")
        
        client = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=key)
        return self._openai_chat(client, os.getenv("GITHUB_MODEL_NAME", "gpt-4o"), prompt, json_mode)

    def _openai_chat(self, client, model_name, prompt, json_mode):
        messages = [{"role": "user", "content": prompt}]
        if json_mode:
            # Enforce JSON structure via system prompt since not all support response_format
            messages.insert(0, {"role": "system", "content": "You are a JSON generator. Output ONLY valid JSON."})
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"} if json_mode and "gpt" in model_name else None
        )
        content = response.choices[0].message.content
        if json_mode:
            # Clean up markdown code blocks if present
            clean_content = content.strip()
            if clean_content.startswith("```"):
                clean_content = clean_content.split("\n", 1)[1]
                if clean_content.endswith("```"):
                    clean_content = clean_content.rsplit("\n", 1)[0]
            clean_content = clean_content.strip()
            
            try:
                return json.loads(clean_content)
            except json.JSONDecodeError:
                print(f"[ERROR] Failed to parse JSON: {content[:100]}...")
                # Attempt to find the first '{' and last '}'
                try:
                    start = clean_content.find('{')
                    end = clean_content.rfind('}') + 1
                    if start != -1 and end != 0:
                        return json.loads(clean_content[start:end])
                except:
                    pass
                raise
        return content

if __name__ == "__main__":
    llm = LLMManager()
    print(llm.generate("Return a JSON with key 'status' and value 'working'", json_mode=True))
