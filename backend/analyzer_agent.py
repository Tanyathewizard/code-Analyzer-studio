# analyzer_agent.py

from ir_model import IRModel
from semantic_extractor import SemanticExtractor


class UnifiedAnalyzer:

    def __init__(self):
        self.ir_agent = IRModel()                 # Your IR generator
        self.semantic_agent = SemanticExtractor() # Your Gemini semantic analyzer

    def analyze(self, code: str, language: str = "python"):
        """
        Unified pipeline:
        Step 1 → IR generation (CFG, DFG, Symbol Table)
        Step 2 → Semantic analysis (with API fallback)
        Step 3 → Merge results
        """
        # ---- Step 1: IR ----
        ir_result = self.ir_agent.build_ir(code, language)

        # ---- Step 2: Semantic ----
        semantic_result = self.semantic_agent.run(code, language)

        # ---- Step 3: Merge ----
        final = {
            "language": language,
            "ir": ir_result,
            "semantic": semantic_result
        }

        return final
