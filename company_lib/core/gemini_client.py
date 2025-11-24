"""
Klient do komunikacji z Google Gemini API.
Używany do analizy i kategoryzacji notatek.
"""
import json
from typing import Dict, Optional, Any
import google.generativeai as genai
from company_lib.config import Config
from company_lib.core.llm_service import ILLMClient
from company_lib.logger import setup_logger

logger = setup_logger("GeminiClient")

class GeminiClient(ILLMClient):
    """
    Klient do komunikacji z Google Gemini API.
    """
    
    def __init__(self):
        """Inicjalizuje klienta Gemini."""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY nie jest skonfigurowany w .env")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config={
                "temperature": Config.GEMINI_TEMPERATURE,
                "max_output_tokens": 1000,
            }
        )
        logger.info(f"Zainicjalizowano Gemini klienta z modelem: {Config.GEMINI_MODEL}")
    
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
            response = self.model.generate_content(prompt)
            
            # Parsowanie odpowiedzi JSON
            response_text = response.text.strip()
            
            # Usuń markdown code blocks jeśli są
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            logger.debug(f"Analiza notatki: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania odpowiedzi JSON z Gemini: {e}")
            logger.debug(f"Odpowiedź: {response_text if 'response_text' in locals() else 'brak'}")
            # Zwróć bezpieczną domyślną odpowiedź
            return {
                "mentions_sample": False,
                "sample_status": "unknown",
                "customer_satisfaction": "unknown",
                "category": "other",
                "confidence": 0.0,
                "reasoning": f"Błąd parsowania odpowiedzi: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Błąd komunikacji z Gemini: {e}", exc_info=True)
            return {
                "mentions_sample": False,
                "sample_status": "unknown",
                "customer_satisfaction": "unknown",
                "category": "other",
                "confidence": 0.0,
                "reasoning": f"Błąd: {str(e)}"
            }
    
    def analyze_notes_batch(self, notes: list, sample_date: str) -> list:
        """
        Analizuje wiele notatek jednocześnie (opcjonalnie, dla wydajności).
        
        Args:
            notes: Lista notatek (obiekty z atrybutem content)
            sample_date: Data wysłania próbki
        
        Returns:
            Lista wyników analizy dla każdej notatki
        """
        results = []
        for note in notes:
            analysis = self.analyze_note_for_sample(note.content, sample_date)
            analysis['note_id'] = note.id
            results.append(analysis)
        return results

