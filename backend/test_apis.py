"""Test which APIs are working"""

import sys
from api_config import APIConfig
from wrapper import openai_analyze_semantic, llama_extract_json, gemini_analyze_code

test_prompt = "Return this JSON: {'test': 'success'}"

print("=" * 60)
print("API CONFIGURATION TEST")
print("=" * 60)

valid, msg = APIConfig.validate()
print(f"\n{msg}")
print(f"Active APIs: {APIConfig.get_active_apis()}")
print(f"Strategy: {APIConfig.API_STRATEGY}")

print("\n" + "=" * 60)
print("TESTING EACH API")
print("=" * 60)

# Test OpenAI
if "openai" in APIConfig.get_active_apis():
    print("\n[OpenAI] Testing...")
    try:
        result = openai_analyze_semantic(test_prompt)
        print(f"✓ OpenAI responded: {result[:200]}")
    except Exception as e:
        print(f"✗ OpenAI failed: {e}")

# Test LLaMA
if "llama" in APIConfig.get_active_apis():
    print("\n[LLaMA] Testing...")
    try:
        result = llama_extract_json(test_prompt)
        print(f"✓ LLaMA responded: {result}")
    except Exception as e:
        print(f"✗ LLaMA failed: {e}")

# Test Gemini
if "gemini" in APIConfig.get_active_apis():
    print("\n[Gemini] Testing...")
    try:
        result = gemini_analyze_code("python", "print('test')")
        print(f"✓ Gemini responded: {result}")
    except Exception as e:
        print(f"✗ Gemini failed: {e}")

print("\n" + "=" * 60)
