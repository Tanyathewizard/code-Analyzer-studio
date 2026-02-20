class AssistantAgent:
    def __init__(self, name="assistant"):
        self.name = name
    def reset(self):
        pass
    def send(self, c):
        return c

class UserProxyAgent:
    def __init__(self, name="user_proxy", code_execution_config=None):
        self.name = name
        self.code_execution_config = code_execution_config or {}
    def reset(self):
        pass
    def initiate_chat(self, recipient, message, max_turns=1):
        msgs = [{"role": "user", "content": message}]
        r = recipient.generate_reply(msgs, sender=self)
        return ChatResult([r])

class ChatResult:
    def __init__(self, messages):
        self.messages = messages
