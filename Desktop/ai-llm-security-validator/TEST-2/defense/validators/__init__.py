from abc import ABC, abstractmethod

class BaseValidator(ABC):
    id: str
    description: str
    severity: str

    @abstractmethod
    def validate(self, response: str, context: dict) -> dict:
        """
        Returns:
        {
          "triggered": bool,
          "confidence": float,
          "evidence": str
        }
        """
        pass