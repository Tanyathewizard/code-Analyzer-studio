import json
from backend.semantic_extractor import SemanticExtractor

SEMANTIC_PROMPT_HUMAN = """
Explain this code clearly:
{code}
"""

class SemanticExtractorAgent:
    def __init__(self, name="semantic_extractor"):
        self.name = name
        self.semantic_extractor = SemanticExtractor()

    def generate_reply(self, messages, sender=None, config=None):
        try:
            msg = messages[-1]["content"].strip()
            if "||SEMANTICS||" not in msg:
                return {"role": "assistant", "content": "Format: <language>||SEMANTICS||<code>"}

            lang, rest = msg.split("||SEMANTICS||", 1)
            lang = lang.strip()

            if "||MODE=HUMAN||" in rest:
                mode = "human"
                code = rest.replace("||MODE=HUMAN||", "").strip()
            else:
                mode = "json"
                code = rest.strip()

            if mode == "json":
                # Use SemanticExtractor with full API fallback strategy
                result = self.semantic_extractor.run(code, lang)
                return {"role": "assistant", "content": json.dumps(result, indent=2)}
            else:
                # For human mode, use the simpler prompt
                prompt = SEMANTIC_PROMPT_HUMAN.format(code=code)
                result = self.semantic_extractor.run(code, lang)  # Use JSON result for now
                return {"role": "assistant", "content": json.dumps(result, indent=2)}

        except Exception as e:
            return {"role": "assistant", "content": f"Semantic Error: {e}"}
