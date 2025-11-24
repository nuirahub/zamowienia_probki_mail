"""
Klient do komunikacji z OpenAI API.
Używany do analizy i kategoryzacji notatek.
"""
import json
from typing import Dict, Any
from openai import OpenAI
from company_lib.config import Config
from company_lib.core.llm_service import ILLMClient
from company_lib.logger import setup_logger

logger = setup_logger("OpenAIClient")

class OpenAIClient(ILLMClient):
    """
    Klient do komunikacji z OpenAI API.
    """
    
    def __init__(self):
        """Inicjalizuje klienta OpenAI."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY nie jest skonfigurowany w .env")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        logger.info(f"Zainicjalizowano OpenAI klienta z modelem: {self.model}")
    
    def analyze_note_for_sample(self, note_content: str, sample_date: str) -> Dict[str, Any]:
        """
        Analizuje notatkę pod kątem informacji o próbce.
        
        Args:
            note_content: Treść notatki
            sample_date: Data wysłania próbki (format: YYYY-MM-DD)
        
        Returns:
            Słownik z wynikami analizy
        """
        prompt = f"""Jesteś ekspertem w analizie notatek biznesowych. Przeanalizuj poniższą notatkę pod kątem informacji o próbce produktu.

Data wysłania próbki: {sample_date}

Treść notatki:
"{note_content}"

Przeanalizuj notatkę i odpowiedz TYLKO w formacie JSON (bez dodatkowego tekstu):
{{
    "mentions_sample": true/false,  // Czy notatka w ogóle wspomina o próbce?
    "sample_status": "received" | "delayed" | "not_received" | "unknown",  // Status próbki
    "customer_satisfaction": "satisfied" | "unsatisfied" | "neutral" | "unknown",  // Zadowolenie klienta
    "category": "sample_confirmation" | "sample_delay" | "sample_complaint" | "sample_inquiry" | "other",  // Kategoria notatki
    "confidence": 0.0-1.0,  // Poziom pewności analizy
    "reasoning": "krótkie uzasadnienie w języku polskim"  // Dlaczego tak skategoryzowano
}}

Zasady:
- "mentions_sample": true tylko jeśli notatka wyraźnie wspomina o próbce/próbkach
- "sample_status": 
  * "received" - klient potwierdził otrzymanie próbki
  * "delayed" - jest mowa o opóźnieniu w dostawie
  * "not_received" - klient zgłasza, że nie otrzymał próbki
  * "unknown" - nie można określić statusu
- "customer_satisfaction":
  * "satisfied" - klient jest zadowolony z próbki
  * "unsatisfied" - klient jest niezadowolony
  * "neutral" - brak informacji o zadowoleniu
  * "unknown" - nie można określić
- "category": wybierz najbardziej pasującą kategorię
- "confidence": 0.0-1.0, gdzie 1.0 to całkowita pewność

Odpowiedz TYLKO JSON, bez dodatkowych komentarzy."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w analizie notatek biznesowych. Zawsze odpowiadasz TYLKO w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            result = json.loads(response_text)
            
            logger.debug(f"Analiza notatki (OpenAI): {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania odpowiedzi JSON z OpenAI: {e}")
            logger.debug(f"Odpowiedź: {response_text if 'response_text' in locals() else 'brak'}")
            return self._default_response(f"Błąd parsowania odpowiedzi: {str(e)}")
        except Exception as e:
            logger.error(f"Błąd komunikacji z OpenAI: {e}", exc_info=True)
            return self._default_response(f"Błąd: {str(e)}")
    
    def _default_response(self, error_msg: str) -> Dict[str, Any]:
        """Zwraca domyślną odpowiedź w przypadku błędu."""
        return {
            "mentions_sample": False,
            "sample_status": "unknown",
            "customer_satisfaction": "unknown",
            "category": "other",
            "confidence": 0.0,
            "reasoning": error_msg
        }

