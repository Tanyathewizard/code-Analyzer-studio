# unified_agent.py
"""
Unified analyzer that uses:
 - IRModel (local static Python analysis)
 - SemanticExtractor (calls LLaMA for Python, Gemini for other languages)
"""

from ir_model import IRModel
from semantic_extractor import SemanticExtractor


class UnifiedAnalyzer:
    def __init__(self, llama_fn=None, gemini_fn=None):
        """
        llama_fn: callable(prompt: str) -> str  (should return text containing JSON)
        gemini_fn: callable(language: str, code: str) -> str  (should return text containing JSON)
        If None, SemanticExtractor will attempt to call wrappers that may return error dicts.
        """
        self.ir_agent = IRModel()
        # SemanticExtractor will internally call the correct wrapper depending on language.
        self.semantic_agent = SemanticExtractor(llama_fn=llama_fn, gemini_fn=gemini_fn)

    def run(self, mode: str, language: str, code: str):
        mode = (mode or "").upper().strip()

        if mode == "IR":
            return self.ir_agent.build_ir(code, language)

        elif mode == "SEMANTIC":
            return self.semantic_agent.run(code, language)

        elif mode == "FULL":
            return {
                "IR": self.ir_agent.build_ir(code, language),
                "SEMANTIC": self.semantic_agent.run(code, language),
            }

        else:
            return {"error": "Invalid mode. Use IR / SEMANTIC / FULL"}
