# Uniwersalny Serwis LLM

System obsługuje wielu dostawców LLM do analizy notatek: **Gemini**, **OpenAI** i **Qwen**.

## Architektura

System używa wzorca **Strategy** - wszystkie dostawcy implementują wspólny interfejs `ILLMClient`:

```
ILLMClient (interfejs)
├── GeminiClient
├── OpenAIClient
└── QwenClient
```

Fabryka `LLMService` automatycznie tworzy odpowiedni klient na podstawie konfiguracji.

## Konfiguracja

### 1. Wybór dostawcy

W pliku `.env` ustaw:

```ini
# Wybór dostawcy LLM: "gemini", "openai" lub "qwen"
LLM_PROVIDER=gemini
```

### 2. Konfiguracja Gemini

```ini
GEMINI_API_KEY=twoj_klucz_gemini
GEMINI_MODEL=gemini-1.5-flash  # Opcjonalnie
GEMINI_TEMPERATURE=0.3  # Opcjonalnie
```

**Uzyskanie klucza:**
1. Przejdź do [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Utwórz klucz API

### 3. Konfiguracja OpenAI

```ini
OPENAI_API_KEY=twoj_klucz_openai
OPENAI_MODEL=gpt-4o-mini  # Opcjonalnie, domyślnie: gpt-4o-mini
OPENAI_TEMPERATURE=0.3  # Opcjonalnie
```

**Uzyskanie klucza:**
1. Przejdź do [OpenAI Platform](https://platform.openai.com/api-keys)
2. Utwórz klucz API

### 4. Konfiguracja Qwen

```ini
QWEN_API_KEY=twoj_klucz_qwen
QWEN_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation  # URL do API
QWEN_MODEL=qwen-turbo  # Opcjonalnie
QWEN_TEMPERATURE=0.3  # Opcjonalnie
```

**Uzyskanie klucza:**
1. Przejdź do [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/)
2. Utwórz klucz API

## Użycie w kodzie

### Podstawowe użycie (domyślny dostawca z Config)

```python
from company_lib.core.llm_service import LLMService

# Używa Config.LLM_PROVIDER
llm_client = LLMService.get_client()
analysis = llm_client.analyze_note_for_sample(note_content, sample_date)
```

### Wybór konkretnego dostawcy

```python
# Użyj Gemini
llm_client = LLMService.get_client("gemini")

# Użyj OpenAI
llm_client = LLMService.get_client("openai")

# Użyj Qwen
llm_client = LLMService.get_client("qwen")
```

### W skrypcie sample_followup.py

```python
# Używa domyślnego dostawcy z Config.LLM_PROVIDER
analysis_result = analyze_notes_with_llm(
    all_notes,
    sample.customer_id,
    sample.date_sent,
    llm_provider=None
)

# Lub wybierz konkretny dostawca
analysis_result = analyze_notes_with_llm(
    all_notes,
    sample.customer_id,
    sample.date_sent,
    llm_provider="openai"  # lub "qwen"
)
```

## Format odpowiedzi

Wszyscy dostawcy zwracają ten sam format:

```python
{
    "mentions_sample": bool,  # Czy notatka wspomina o próbce?
    "sample_status": str,  # "received", "delayed", "not_received", "unknown"
    "customer_satisfaction": str,  # "satisfied", "unsatisfied", "neutral", "unknown"
    "category": str,  # "sample_confirmation", "sample_delay", "sample_complaint", "sample_inquiry", "other"
    "confidence": float,  # 0.0-1.0
    "reasoning": str  # Uzasadnienie w języku polskim
}
```

## Porównanie dostawców

| Cecha | Gemini | OpenAI | Qwen |
|-------|--------|--------|------|
| **Darmowy tier** | ✅ Tak (15 RPM) | ❌ Nie | ✅ Tak (ograniczony) |
| **Jakość analizy** | Wysoka | Bardzo wysoka | Wysoka |
| **Szybkość** | Szybka | Średnia | Szybka |
| **Obsługa polskiego** | Dobra | Bardzo dobra | Dobra |
| **Koszt** | Darmowy (limit) | Płatny | Płatny (tanie) |

## Rekomendacje

- **Dla prototypu/testów:** Gemini (darmowy)
- **Dla produkcji (wysoka jakość):** OpenAI GPT-4o-mini
- **Dla produkcji (niski koszt):** Qwen

## Przykład przełączania

```python
# W sample_followup.py, linia ~150
analysis_result = analyze_notes_with_llm(
    all_notes,
    sample.customer_id,
    sample.date_sent,
    llm_provider="openai"  # Zmień tutaj: "gemini", "openai" lub "qwen"
)
```

Lub zmień domyślny dostawca w `.env`:
```ini
LLM_PROVIDER=openai
```

## Troubleshooting

### Błąd: "Nieobsługiwany dostawca LLM"
- Sprawdź czy nazwa dostawcy jest poprawna: `"gemini"`, `"openai"` lub `"qwen"`
- Nazwy są case-insensitive

### Błąd: "API_KEY nie jest skonfigurowany"
- Sprawdź czy odpowiedni klucz API jest w pliku `.env`
- Upewnij się, że nazwa zmiennej jest poprawna (np. `GEMINI_API_KEY`, `OPENAI_API_KEY`)

### Błąd parsowania JSON
- Wszyscy dostawcy powinni zwracać JSON, ale czasem format może się różnić
- Sprawdź logi dla pełnej odpowiedzi API
- Kod automatycznie usuwa markdown code blocks

## Rozszerzanie o nowych dostawców

Aby dodać nowego dostawcę:

1. Stwórz klasę dziedziczącą po `ILLMClient`:
```python
from company_lib.core.llm_service import ILLMClient

class NewProviderClient(ILLMClient):
    def analyze_note_for_sample(self, note_content: str, sample_date: str) -> Dict[str, Any]:
        # Implementacja
        pass
```

2. Dodaj do `LLMService.get_client()`:
```python
elif model_provider == "newprovider":
    from company_lib.core.new_provider_client import NewProviderClient
    return NewProviderClient()
```

3. Dodaj konfigurację do `config.py`

