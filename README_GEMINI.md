# Integracja z Google Gemini AI

Skrypt `sample_followup.py` używa Google Gemini AI do inteligentnej analizy notatek pod kątem informacji o próbkach produktów.

## Konfiguracja

### 1. Uzyskaj klucz API Gemini

1. Przejdź do [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Zaloguj się kontem Google
3. Utwórz nowy klucz API
4. Skopiuj klucz

### 2. Dodaj klucz do `.env`

```ini
# Konfiguracja Gemini AI
GEMINI_API_KEY=twoj_klucz_api_tutaj
GEMINI_MODEL=gemini-1.5-flash  # Opcjonalnie, domyślnie: gemini-1.5-flash
GEMINI_TEMPERATURE=0.3  # Opcjonalnie, domyślnie: 0.3 (niższa = bardziej deterministyczne odpowiedzi)
```

### 3. Zainstaluj zależności

```bash
pip install -e .
```

## Jak działa analiza

### Funkcja `analyze_notes_with_gemini()`

Funkcja analizuje notatki używając Gemini AI i zwraca szczegółowe informacje:

```python
{
    "has_confirmation": bool,  # Czy jest jakiekolwiek potwierdzenie
    "sample_received": bool,  # Czy próbka dotarła
    "has_delay": bool,  # Czy jest opóźnienie
    "customer_satisfied": Optional[bool],  # Czy klient jest zadowolony
    "best_note_analysis": Dict,  # Analiza najlepszej notatki
    "all_analyses": List[Dict]  # Wszystkie analizy
}
```

### Kategorie notatek

Gemini kategoryzuje notatki jako:
- `sample_confirmation` - potwierdzenie otrzymania próbki
- `sample_delay` - opóźnienie w dostawie
- `sample_complaint` - reklamacja dotycząca próbki
- `sample_inquiry` - zapytanie o próbkę
- `other` - inne

### Statusy próbki

- `received` - klient potwierdził otrzymanie
- `delayed` - jest mowa o opóźnieniu
- `not_received` - klient zgłasza brak próbki
- `unknown` - nie można określić

### Zadowolenie klienta

- `satisfied` - klient jest zadowolony
- `unsatisfied` - klient jest niezadowolony
- `neutral` - brak informacji
- `unknown` - nie można określić

## Przykłady działania

### Przykład 1: Potwierdzenie otrzymania
**Notatka:** "Klient dzwonił, próbki dotarły i są super."

**Wynik Gemini:**
```json
{
    "mentions_sample": true,
    "sample_status": "received",
    "customer_satisfaction": "satisfied",
    "category": "sample_confirmation",
    "confidence": 0.95
}
```

**Akcja:** Próbka nie wymaga weryfikacji, zadanie nie zostanie utworzone.

### Przykład 2: Opóźnienie
**Notatka:** "Klient pyta gdzie są próbki, wysłaliśmy je tydzień temu."

**Wynik Gemini:**
```json
{
    "mentions_sample": true,
    "sample_status": "delayed",
    "customer_satisfaction": "unsatisfied",
    "category": "sample_delay",
    "confidence": 0.90
}
```

**Akcja:** Utworzy zadanie typu `SAMPLE_DELAY` z informacją o opóźnieniu.

### Przykład 3: Brak informacji
**Notatka:** "Klient prosi o przesłanie katalogu produktów."

**Wynik Gemini:**
```json
{
    "mentions_sample": false,
    "sample_status": "unknown",
    "customer_satisfaction": "unknown",
    "category": "other",
    "confidence": 0.85
}
```

**Akcja:** Utworzy standardowe zadanie typu `SAMPLE_FOLLOWUP`.

## Typy zadań

W zależności od analizy Gemini, skrypt tworzy różne typy zadań:

1. **SAMPLE_FOLLOWUP** - standardowa weryfikacja (brak informacji w notatkach)
2. **SAMPLE_DELAY** - wykryto opóźnienie w dostawie
3. **SAMPLE_VERIFICATION** - jest mowa o próbce, ale brak potwierdzenia

## Logowanie

Skrypt loguje szczegółowe informacje o analizie:

```
INFO: Analizuję 3 notatek dla klienta CUST_001 używając Gemini
INFO: Wynik analizy Gemini dla klienta CUST_001: status=received, satisfaction=satisfied, confidence=0.95
```

## Koszty API

Gemini 1.5 Flash jest darmowy do pewnego limitu:
- 15 RPM (requests per minute)
- 1M TPM (tokens per minute)
- 1000 RPD (requests per day)

Dla większych wolumenów rozważ użycie `gemini-1.5-pro` (płatny).

## Troubleshooting

### Błąd: "GEMINI_API_KEY nie jest skonfigurowany"
- Sprawdź czy klucz jest w pliku `.env`
- Upewnij się, że plik `.env` jest w głównym katalogu projektu

### Błąd parsowania JSON
- Gemini czasem zwraca odpowiedź w markdown, kod automatycznie to obsługuje
- Jeśli problem się powtarza, sprawdź logi dla pełnej odpowiedzi

### Niska pewność analizy
- Zwiększ `GEMINI_TEMPERATURE` w `.env` (np. 0.5-0.7)
- Upewnij się, że notatki są w języku polskim i zawierają istotne informacje

