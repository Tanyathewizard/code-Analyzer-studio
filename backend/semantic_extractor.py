# semantic_extractor.py
"""
Semantic extractor that:
 - builds a prompt (with braces escaped so .format won't break)
 - calls wrapper functions based on API_STRATEGY in .env
 - extracts the first JSON object found in the text response and returns a dict
"""
import re
import json
import logging
import os
from typing import Any, Callable, Optional

from backend.api_config import APIConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The prompt uses doubled braces for literal JSON so .format() doesn't try to substitute them.
SEMANTIC_PROMPT = """
You are a senior software architect and semantic analyzer.

Return ONLY valid JSON that matches the schema shown below.

SCHEMA:
{{
  "purpose": "",
  "name": "",
  "description": "",
  "inputs": [],
  "outputs": [],
  "complexity_estimate": "",
  "dependencies": [],
  "patterns": [],
  "edge_cases": [],
  "optimizations": [],
  "variable_roles": {{ }},
  "functions": [],
  "summary": ""
}}

Analyze this {language} code:
---------------------
{code}
---------------------
Please return ONLY one JSON object (no extra commentary). If you cannot, still include a JSON object with an 'error' field.
"""

def extract_json_only(text: str) -> str:
    """
    Return the first {...} block found in text. If none, return "{}".
    Uses a balanced-brace scan to avoid greedy regex issues.
    """
    if not text:
        return "{}"
    t = text.replace("```json", "").replace("```", "").strip()
    start = t.find("{")
    if start == -1:
        return "{}"
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                return t[start:i+1]
    # fallback to regex if balance scan fails
    matches = re.findall(r"\{[\s\S]*?\}", t)
    return matches[0] if matches else "{}"

class SemanticExtractor:
    def __init__(self, openai_fn: Optional[Callable[[str], str]] = None,
                 llama_fn: Optional[Callable[[str], str]] = None,
                 gemini_fn: Optional[Callable[[str, str], str]] = None):
        """
        Semantic extractor with smart API fallback:
        1. Try OpenAI (primary)
        2. Fallback to LLaMA/OpenRouter (cheaper)
        3. Fallback to Gemini (last resort)
        """
        self.openai_fn = openai_fn
        self.llama_fn = llama_fn
        self.gemini_fn = gemini_fn
        # timeout per API (seconds) — configurable via env var
        try:
            self.timeout_per_api = int(os.getenv("SEMANTIC_API_TIMEOUT", "8"))
        except Exception:
            self.timeout_per_api = 8

    def _ensure_wrappers(self):
        """Load wrapper functions from wrapper.py at runtime"""
        if not self.openai_fn:
            try:
                from wrapper import openai_analyze_semantic
                self.openai_fn = openai_analyze_semantic
            except Exception:
                self.openai_fn = None

        if not self.llama_fn:
            try:
                from wrapper import llama_extract_json
                self.llama_fn = llama_extract_json
            except Exception:
                self.llama_fn = None

        if not self.gemini_fn:
            try:
                from wrapper import gemini_analyze_code
                self.gemini_fn = gemini_analyze_code
            except Exception:
                self.gemini_fn = None

    def build_prompt(self, code: str, language: str) -> str:
        return SEMANTIC_PROMPT.format(code=code, language=language)

    def run(self, code: str, language: str = "python", mode: str = "json") -> Any:
        """
        Semantic analysis with configurable API fallback chain.
        Uses API_STRATEGY from .env to try APIs sequentially (one at a time).
        Stops at first success. Only moves to next if current fails.

        Returns a dict (parsed JSON) or an error dict.
        TIMEOUT: configurable per API (env SEMANTIC_API_TIMEOUT), default 8s
        """
        from threading import Thread
        import time

        self._ensure_wrappers()
        prompt = self.build_prompt(code, language)
        lang = (language or "python").strip().lower()

        active_apis = APIConfig.get_active_apis()
        if not active_apis:
            logger.info("No APIs configured, using fallback extraction")
            return self._extract_basic_semantic(code, language)

        logger.info(f"API Strategy: {' → '.join([api.upper() for api in active_apis])} ({self.timeout_per_api}s per API)")

        # Try each API in strategy order - SEQUENTIALLY, one at a time
        for api_name in active_apis:
            try:
                result_container = {"raw": None, "done": False}

                def api_call():
                    """Call API in separate thread to enable timeout"""
                    try:
                        # Call appropriate API
                        if api_name == "openai" and self.openai_fn:
                            logger.debug("Calling OpenAI...")
                            result_container["raw"] = self.openai_fn(prompt)
                        elif api_name == "llama" and self.llama_fn:
                            logger.debug("Calling LLaMA/OpenRouter...")
                            result_container["raw"] = self.llama_fn(prompt)
                        elif api_name == "gemini" and self.gemini_fn:
                            logger.debug("Calling Gemini...")
                            # gemini wrapper expects (lang, code)
                            result_container["raw"] = self.gemini_fn(lang, code)
                        elif api_name == "groq" and hasattr(self, 'groq_fn') and self.groq_fn:
                            result_container["raw"] = self.groq_fn(prompt)
                        else:
                            result_container["done"] = True
                            return
                    except Exception:
                        logger.exception(f"Exception when calling {api_name}")
                    finally:
                        result_container["done"] = True

                # Run API call in thread with configurable timeout
                thread = Thread(target=api_call, daemon=True)
                thread.start()
                thread.join(timeout=self.timeout_per_api)

                if not result_container["done"] or result_container["raw"] is None:
                    logger.warning(f"[{api_name.upper()}] timeout/failed or returned None, trying next...")
                    continue

                # Log raw response for debugging (trimmed)
                raw_preview = str(result_container["raw"])
                logger.debug(f"[{api_name.upper()}] raw preview: {raw_preview[:1000]}")

                # Parse response
                parsed = self._parse_json_response(result_container["raw"])

                # If successful JSON, return immediately (no 'error' field)
                if isinstance(parsed, dict) and "error" not in parsed:
                    logger.info(f"✓ [{api_name.upper()}] SUCCESS")
                    return parsed

                logger.warning(f"[{api_name.upper()}] parse result contained error or invalid JSON: {parsed.get('error') if isinstance(parsed, dict) else 'parse failed'}")
            except Exception:
                logger.exception(f"[{api_name.upper()}] unexpected error")
                continue

        # All APIs failed or timeout - use fallback
        logger.info("Using fallback semantic extraction (fast, local analysis)")
        return self._extract_basic_semantic(code, language)

    def _extract_basic_semantic(self, code: str, language: str) -> dict:
        """Extract basic semantic info from code without API calls (fast fallback)"""
        import re

        lines = code.split('\n')

        # Extract function/class names
        functions = re.findall(r'def\s+(\w+)', code)
        classes = re.findall(r'class\s+(\w+)', code)

        return {
            "purpose": "Fast semantic analysis (API timeout fallback)",
            "name": functions[0] if functions else classes[0] if classes else "Unknown",
            "description": f"Analyzed {language} code ({len(lines)} lines)",
            "inputs": functions[:3] if functions else [],
            "outputs": classes[:3] if classes else [],
            "complexity_estimate": "O(n)" if "for " in code or "while " in code else "O(1)",
            "dependencies": [],
            "patterns": ["sequential"] if "for " in code or "while " in code else [],
            "edge_cases": [],
            "optimizations": [],
            "variable_roles": {},
            "functions": functions,
            "summary": f"Contains {len(functions)} functions and {len(classes)} classes"
        }

    def _parse_json_response(self, raw: Any) -> Any:
        """Parse JSON response from any API"""
        if isinstance(raw, dict):
            return raw
        try:
            txt = str(raw)
            jtxt = extract_json_only(txt)
            parsed = json.loads(jtxt)
            return parsed
        except json.JSONDecodeError:
            return {"error": "JSON parse failed", "raw": str(raw)[:200]}
        except Exception as e:
            return {"error": f"Parse error: {e}", "raw": str(raw)[:200]}
