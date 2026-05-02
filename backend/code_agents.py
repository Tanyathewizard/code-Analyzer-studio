import json
from backend.agents_base import AssistantAgent, UserProxyAgent
from backend.semantic_extractor import SemanticExtractor

class CodeAnalyzerAgent(AssistantAgent):
    def __init__(self, name="code_analyzer"):
        super().__init__(name=name)
        self.semantic_extractor = SemanticExtractor()

    def generate_reply(self, messages, sender, config=None):
        try:
            msg = messages[-1]["content"].strip()
            if "||CODE||" not in msg:
                return {"role": "assistant", "content": "Format: <language>||CODE||<code>||MODE=(JSON/HUMAN)"}
            if "||MODE=HUMAN||" in msg:
                mode = "human"
                m = msg.replace("||MODE=HUMAN||", "")
            else:
                mode = "json"
                m = msg
            lang, code = m.split("||CODE||", 1)
            lang = lang.strip()
            code = code.strip()
            
            # Use SemanticExtractor with full API fallback strategy
            result = self.semantic_extractor.run(code, lang)
            
            if mode == "json":
                return {"role": "assistant", "content": json.dumps(result, indent=2)}
            else:
                return {"role": "assistant", "content": str(result)}
        except Exception as e:
            return {"role": "assistant", "content": f"Analyzer Error: {e}"}

def create_agents():
    u = UserProxyAgent(name="user_proxy", code_execution_config={"use_docker": False})
    a = CodeAnalyzerAgent(name="code_analyzer")
    return u, a
