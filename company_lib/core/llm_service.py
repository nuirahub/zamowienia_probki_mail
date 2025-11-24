"""
Uniwersalny serwis LLM z obsługą różnych dostawców (Gemini, OpenAI, Qwen).
Używa wzorca Strategy - każdy dostawca implementuje wspólny interfejs.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from company_lib.config import Config
from company_lib.logger import setup_logger

logger = setup_logger("LLMService")

class ILLMClient(ABC):
    """
    Abstrakcyjna klasa bazowa dla wszystkich klientów LLM.
    Definiuje wspólny interfejs dla analizy notatek.
    """
    
    @abstractmethod
    def analyze_note_for_sample(self, note_content: str, sample_date: str) -> Dict[str, Any]:
        """
        Analizuje notatkę pod kątem informacji o próbce.
        
        Args:
            note_content: Treść notatki
            sample_date: Data wysłania próbki (format: YYYY-MM-DD)
        
        Returns:
            Słownik z wynikami analizy:
            {
                "mentions_sample": bool,
                "sample_status": str,  # "received", "delayed", "not_received", "unknown"
                "customer_satisfaction": str,  # "satisfied", "unsatisfied", "neutral", "unknown"
                "category": str,  # Kategoria notatki
                "confidence": float,  # 0.0-1.0
                "reasoning": str  # Krótkie uzasadnienie
            }
        """
        pass


class LLMService:
    """
    Fabryka do tworzenia odpowiedniego klienta LLM na podstawie konfiguracji.
    """
    
    @staticmethod
    def get_client(model_provider: Optional[str] = None) -> ILLMClient:
        """
        Tworzy i zwraca odpowiedni klient LLM.
        
        Args:
            model_provider: Nazwa dostawcy ("gemini", "openai", "qwen")
                          Jeśli None, używa wartości z Config.LLM_PROVIDER
        
        Returns:
            Instancja klienta LLM implementująca ILLMClient
        
        Raises:
            ValueError: Jeśli dostawca nie jest obsługiwany lub brak konfiguracji
        """
        if model_provider is None:
            model_provider = Config.LLM_PROVIDER.lower()
        
        model_provider = model_provider.lower()
        
        if model_provider == "gemini":
            from company_lib.core.gemini_client import GeminiClient
            logger.info("Tworzenie klienta Gemini")
            return GeminiClient()
        
        elif model_provider == "openai":
            from company_lib.core.openai_client import OpenAIClient
            logger.info("Tworzenie klienta OpenAI")
            return OpenAIClient()
        
        elif model_provider == "qwen":
            from company_lib.core.qwen_client import QwenClient
            logger.info("Tworzenie klienta Qwen")
            return QwenClient()
        
        else:
            raise ValueError(
                f"Nieobsługiwany dostawca LLM: {model_provider}. "
                f"Dostępne: 'gemini', 'openai', 'qwen'"
            )

