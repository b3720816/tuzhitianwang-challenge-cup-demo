from typing import Protocol
class LLMProviderError(RuntimeError): pass
class LLMProvider(Protocol):
    provider_name: str
    def generate_report(self,prompt: str,*,evidence_text: str) -> str: ...
