"""
API Configuration Manager
Allows switching between different API providers and strategies without code changes.
All configuration comes from .env file.
"""

import os
from dotenv import load_dotenv
from typing import List, Literal

load_dotenv()

class APIConfig:
    """Centralized API configuration"""
    
    # API provider options
    OPENAI_KEY = os.getenv("API_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    LLAMA_KEY = os.getenv("OPENROUTER_API_KEY")
    CLAUDE_KEY = os.getenv("CLAUDE_API_KEY")
    GROQ_KEY = os.getenv("GROQ_API_KEY")
    
    # STRATEGY: which APIs to use and in what order
    # Change this in .env as: API_STRATEGY=openai,gemini,llama
    API_STRATEGY = os.getenv("API_STRATEGY", "openai,gemini,llama").split(",")
    API_STRATEGY = [api.strip().lower() for api in API_STRATEGY]
    
    # RATE LIMITING: requests per minute (per provider)
    OPENAI_RPM = int(os.getenv("OPENAI_RPM", "60"))
    GEMINI_RPM = int(os.getenv("GEMINI_RPM", "60"))
    LLAMA_RPM = int(os.getenv("LLAMA_RPM", "20"))  # Free tier limit
    CLAUDE_RPM = int(os.getenv("CLAUDE_RPM", "60"))
    GROQ_RPM = int(os.getenv("GROQ_RPM", "60"))
    
    # CACHING: enable/disable result caching
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
    
    # RETRY STRATEGY
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "2"))
    
    # MODEL SELECTION
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    LLAMA_MODEL = os.getenv("LLAMA_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
    
    @classmethod
    def get_active_apis(cls) -> List[str]:
        """Return list of enabled APIs in priority order"""
        available = []
        for api in cls.API_STRATEGY:
            if api == "openai" and cls.OPENAI_KEY:
                available.append("openai")
            elif api == "gemini" and cls.GEMINI_KEY:
                available.append("gemini")
            elif api == "llama" and cls.LLAMA_KEY:
                available.append("llama")
            elif api == "claude" and cls.CLAUDE_KEY:
                available.append("claude")
            elif api == "groq" and cls.GROQ_KEY:
                available.append("groq")
        return available
    
    @classmethod
    def get_rpm_limit(cls, api: str) -> int:
        """Get rate limit (requests per minute) for an API"""
        limits = {
            "openai": cls.OPENAI_RPM,
            "gemini": cls.GEMINI_RPM,
            "llama": cls.LLAMA_RPM,
            "claude": cls.CLAUDE_RPM,
            "groq": cls.GROQ_RPM,
        }
        return limits.get(api.lower(), 60)
    
    @classmethod
    def get_model(cls, api: str) -> str:
        """Get model name for an API"""
        models = {
            "openai": cls.OPENAI_MODEL,
            "gemini": cls.GEMINI_MODEL,
            "llama": cls.LLAMA_MODEL,
            "claude": cls.CLAUDE_MODEL,
            "groq": cls.GROQ_MODEL,
        }
        return models.get(api.lower(), "")
    
    @classmethod
    def get_key(cls, api: str) -> str:
        """Get API key for an API"""
        keys = {
            "openai": cls.OPENAI_KEY,
            "gemini": cls.GEMINI_KEY,
            "llama": cls.LLAMA_KEY,
            "claude": cls.CLAUDE_KEY,
            "groq": cls.GROQ_KEY,
        }
        return keys.get(api.lower(), "")
    
    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """Validate that at least one API is configured"""
        active_apis = cls.get_active_apis()
        if not active_apis:
            return False, "No API keys configured. Set at least one of: API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, CLAUDE_API_KEY, GROQ_API_KEY"
        return True, f"✓ Active APIs: {', '.join(active_apis)}"


if __name__ == "__main__":
    valid, msg = APIConfig.validate()
    print(msg)
    if valid:
        print(f"Strategy: {APIConfig.API_STRATEGY}")
        print(f"Active: {APIConfig.get_active_apis()}")
