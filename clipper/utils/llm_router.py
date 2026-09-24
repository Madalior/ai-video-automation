import os
import sys
from pathlib import Path
from openai import OpenAI
from dataclasses import dataclass
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load clipper/.env (this file lives in clipper/utils/, so go up 2 levels)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # fallback to any .env in path

@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    models: list[str]

def get_llm_configs() -> list[LLMConfig]:
    """Parse .env for all LLM providers."""
    configs = []
    # Support up to 5 fallback providers
    for i in range(1, 6):
        base_url = os.getenv(f"LLM_{i}_BASE_URL")
        api_key = os.getenv(f"LLM_{i}_API_KEY")
        models_str = os.getenv(f"LLM_{i}_MODELS")
        
        if base_url and models_str:
            models = [m.strip() for m in models_str.split(",") if m.strip()]
            configs.append(LLMConfig(base_url=base_url, api_key=api_key or "dummy-key", models=models))
            
    # Legacy fallback if they haven't updated .env yet
    if not configs:
        base_url = os.getenv("NVIDIA_BASE_URL", "https://openrouter.ai/api/v1")
        api_key = os.getenv("NVIDIA_API_KEY", "dummy-key")
        models_str = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super:free")
        models = [m.strip() for m in models_str.split(",") if m.strip()]
        configs.append(LLMConfig(base_url=base_url, api_key=api_key, models=models))
        
    return configs

_cached_working_client = None
_cached_working_model = None

def call_llm_with_fallback(messages: list, temperature: float = 0.3, max_tokens: int = 4096, timeout: float = 12.0) -> str:
    global _cached_working_client, _cached_working_model
    
    # 1. Try last known working model first for zero-latency, zero-error execution
    if _cached_working_client is not None and _cached_working_model is not None:
        try:
            response = _cached_working_client.chat.completions.create(
                model=_cached_working_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception:
            _cached_working_client = None
            _cached_working_model = None

    configs = get_llm_configs()
    last_err = None
    
    for config in configs:
        client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        for model in config.models:
            try:
                provider_name = "Groq" if "groq" in config.base_url else ("NVIDIA NIM" if "nvidia" in config.base_url else "OpenRouter")
                print(f"[LLM_ROUTER] 🤖 Routing prompt to {provider_name} ({model})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    _cached_working_client = client
                    _cached_working_model = model
                    return content.strip()
            except Exception as e:
                print(f"[LLM_ROUTER] ⚠️  {model} failed: {e}. Switching...")
                last_err = e
            
    raise Exception(f"All fallback models and providers failed! Last error: {last_err}")


def get_langchain_llm_with_fallbacks():
    from langchain_openai import ChatOpenAI
    
    configs = get_llm_configs()
    llms = []
    
    for config in configs:
        for model in config.models:
            llms.append(ChatOpenAI(
                model=model,
                base_url=config.base_url,
                api_key=config.api_key
            ))
            
    if not llms:
        raise ValueError("No LLM configurations found in .env")
        
    primary = llms[0]
    if len(llms) > 1:
        return primary.with_fallbacks(llms[1:])
    return primary
