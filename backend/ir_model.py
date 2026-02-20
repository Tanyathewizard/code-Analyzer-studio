from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class VariableInfo:
    name: str
    linenos: List[int] = field(default_factory=list)
    assigned: List[int] = field(default_factory=list)
    used: List[int] = field(default_factory=list)

@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    variables: Dict[str, VariableInfo] = field(default_factory=dict)

@dataclass
class ClassInfo:
    name: str
    lineno: int
    methods: Dict[str, FunctionInfo] = field(default_factory=dict)

@dataclass
class IR:
    language: str
    ast: Any
    symbol_table: Dict[str, Any] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    cfg: Dict[str, Any] = field(default_factory=dict)
    dfg: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""

class IRModel:
    def build_ir(self, code: str, language: str = "python") -> Dict[str, Any]:
        language = language.lower()

        # If Python, try offline IR
        if language == "python":
            try:
                from cfg_builder import build_cfg
                from dfg_builder import build_dfg

                symbol_table = {}
                cfg = build_cfg(code)
                dfg = build_dfg(code)

                return {
                    "language": "python",
                    "symbol_table": symbol_table,
                    "cfg": cfg,
                    "dfg": dfg,
                    "error": None
                }

            except Exception:
                # Parsing failed → fallback to Gemini
                language = "gemini"

        # For non-Python or fallback → call SemanticExtractor / Gemini
        try:
            from semantic_extractor import SemanticExtractor
            gemini_agent = SemanticExtractor()
            return gemini_agent.run(code, language)
        except Exception as e:
            return {
                "language": language,
                "symbol_table": {},
                "cfg": {},
                "dfg": {},
                "error": f"Gemini IR failed: {e}"
            }
