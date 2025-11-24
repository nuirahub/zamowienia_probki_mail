"""
Klient do komunikacji z Qwen API (Alibaba Cloud).
Używany do analizy i kategoryzacji notatek.
"""
import json
from typing import Dict, Any
import requests
from company_lib.config import Config
from company_lib.core.llm_service import ILLMClient
from company_lib.logger import setup_logger

logger = setup_logger("QwenClient")

class QwenClient(ILLMClient):
    """
    Klient do komunikacji z Qwen API.
    """
    
    def __init__(self):
        """Inicjalizuje klienta Qwen."""
        if not Config.QWEN_API_KEY:
            raise ValueError("QWEN_API_KEY nie jest skonfigurowany w .env")
        if not Config.QWEN_API_URL:
            raise ValueError("QWEN_API_URL nie jest skonfigurowany w .env")
        
        self.api_key = Config.QWEN_API_KEY
        self.api_url = Config.QWEN_API_URL
        self.model = Config.QWEN_MODEL
        self.temperature = Config.QWEN_TEMPERATURE
        logger.info(f"Zainicjalizowano Qwen klienta z modelem: {self.model}")
    
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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Jesteś ekspertem w analizie notatek biznesowych. Zawsze odpowiadasz TYLKO w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            # Qwen zwraca odpowiedź w różnych formatach, dostosuj do swojego API
            if "choices" in response_data:
                response_text = response_data["choices"][0]["message"]["content"].strip()
            elif "output" in response_data:
                response_text = response_data["output"]["text"].strip()
            else:
                # Próba wyciągnięcia tekstu z odpowiedzi
                response_text = str(response_data).strip()
            
            # Usuń markdown code blocks jeśli są
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            logger.debug(f"Analiza notatki (Qwen): {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania odpowiedzi JSON z Qwen: {e}")
            logger.debug(f"Odpowiedź: {response_text if 'response_text' in locals() else 'brak'}")
            return self._default_response(f"Błąd parsowania odpowiedzi: {str(e)}")
        except Exception as e:
            logger.error(f"Błąd komunikacji z Qwen: {e}", exc_info=True)
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

