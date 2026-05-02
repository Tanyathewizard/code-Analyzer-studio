import os
import json
import time
import requests
import logging
from dotenv import load_dotenv
try:
    import google.generativeai as gen
except:
    gen = None
from openai import OpenAI
from backend.api_config import APIConfig
from backend.api_limiter import apply_rate_limit, should_use_cache, cache_result

load_dotenv()

# Validate configuration
valid, msg = APIConfig.validate()
if not valid:
    logging.warning(msg)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients for available APIs
OPENAI_CLIENT = None
GEMINI_MODEL = None

if APIConfig.OPENAI_KEY:
    try:
        OPENAI_CLIENT = OpenAI(api_key=APIConfig.OPENAI_KEY)
        logger.info("✓ OpenAI client initialized")
    except Exception as e:
        logger.warning(f"Failed to init OpenAI: {e}")

if APIConfig.GEMINI_KEY:
    try:
        gen.configure(api_key=APIConfig.GEMINI_KEY)
        GEMINI_MODEL = gen.GenerativeModel(APIConfig.GEMINI_MODEL)
        logger.info("✓ Gemini client initialized")
    except Exception as e:
        logger.warning(f"Failed to init Gemini: {e}")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_json(text: str):
    if not text:
        return None
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        if len(parts) > 1:
            t = parts[1]
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1:
        return None
    candidate = t[start:end + 1]
    try:
        return json.loads(candidate)
    except:
        pass
    cleaned = candidate.replace("\n", "").replace("\t", "").replace(",}", "}")
    try:
        return json.loads(cleaned)
    except:
        return None

def gemini_send(prompt: str) -> str:
    try:
        if GEMINI_MODEL is None:
            return "Gemini Error: Model not initialized"
        apply_rate_limit("gemini")
        resp = GEMINI_MODEL.generate_content(prompt)
        try:
            return resp.candidates[0].content.parts[0].text
        except:
            pass
        try:
            return resp.candidates[0].content[0].text
        except:
            pass
        return getattr(resp, "text", str(resp))
    except Exception as e:
        return f"Gemini Error: {str(e)}"

def gemini_analyze_code(language: str, code: str) -> dict:
    # Check cache first
    cached = should_use_cache("gemini", code, language)
    if cached:
        logger.info("✓ Cache hit for Gemini")
        return cached
    
    prompt = f"""
Return ONLY JSON: {{ "ast": {{}}, "symbols": {{}}, "cfg": {{}}, "dfg": {{}} }}
Analyze {language} code:
{code}
    """
    raw = gemini_send(prompt)
    parsed = extract_json(raw)
    result = parsed if parsed is not None else {"error": "Gemini returned non-JSON", "raw": raw[:500]}
    
    # Cache result
    cache_result("gemini", code, result, language)
    return result

def openai_analyze_semantic(prompt: str) -> str:
    """
    Analyze code semantics using OpenAI API
    Respects rate limits and uses cache
    """
    try:
        if OPENAI_CLIENT is None:
            return "OpenAI Error: Client not initialized"
        
        apply_rate_limit("openai")
        response = OPENAI_CLIENT.chat.completions.create(
            model=APIConfig.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a code analysis expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=2000,
            timeout=60
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        # Log rate limit errors specifically
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return f"OpenAI Rate Limit: {error_msg}"
        elif "quota" in error_msg.lower():
            return f"OpenAI Quota Exceeded: {error_msg}"
        else:
            return f"OpenAI Error: {error_msg}"

def llama_raw_call(prompt: str, retries=None, backoff=None) -> str:
    if APIConfig.LLAMA_KEY is None:
        return "LLaMA Error: OPENROUTER_API_KEY not configured"
    
    if retries is None:
        retries = APIConfig.MAX_RETRIES
    if backoff is None:
        backoff = APIConfig.RETRY_BACKOFF_FACTOR
    
    headers = {
        "Authorization": f"Bearer {APIConfig.LLAMA_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "AutoAI Semantic Extractor"
    }
    
    payload = {
        "model": APIConfig.LLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    for attempt in range(retries + 1):
        try:
            apply_rate_limit("llama")
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            if "choices" not in data:
                logger.error(f"LLaMA unexpected response: {data}")
                return f"LLaMA Error: 'choices' not in response - {data}"
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"LLaMA attempt {attempt+1} failed: {error_msg}")
            if attempt < retries:
                time.sleep((attempt + 1) * backoff)
            else:
                return f"LLaMA Error: {error_msg}"

def llama_extract_json(prompt: str) -> dict:
    # Check cache first
    cached = should_use_cache("llama", prompt)
    if cached:
        logger.info("✓ Cache hit for LLaMA")
        return cached
    
    raw = llama_raw_call(prompt)
    parsed = extract_json(raw)
    result = parsed if parsed is not None else {"error": "No JSON detected from LLaMA", "raw": raw[:500]}
    
    # Cache result
    cache_result("llama", prompt, result)
    return result
