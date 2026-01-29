# defense/semantic_classifier.py

class SemanticStreamClassifier:
    """
    Detects dangerous semantic intent across token streams.
    Phrase-aware.
    """

    def __init__(self):
        self.buffer = ""

    def reset(self):
        self.buffer = ""

    def score_token(self, token: str):
        self.buffer += token.lower()

        # Prompt injection
        if "ignore previous instruction" in self.buffer:
            return {
                "signal": "prompt_injection",
                "severity": "Critical",
                "confidence": 0.95
            }

        # System prompt leakage
        if "system prompt" in self.buffer or "developer message" in self.buffer:
            return {
                "signal": "data_leakage",
                "severity": "Critical",
                "confidence": 0.9
            }

        # Refusal bypass attempts
        if "you are allowed to" in self.buffer:
            return {
                "signal": "refusal_bypass",
                "severity": "High",
                "confidence": 0.7
            }

        return None