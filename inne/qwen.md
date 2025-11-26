Modele z rodziny Qwen (zakładam, że korzystasz z **Qwen 2.5 7B**, ponieważ "Qwen3" jeszcze oficjalnie nie wyszedł, ale zasady są te same) są świetne, ale przy rozmiarze 7B/8B wymagają bardzo sztywnych ram, aby nie "gadały" (np. nie dodawały wstępów typu "Oto Twój JSON").

Aby zmusić model do posłuszeństwa, musisz przenieść ciężar definicji formatu do **System Message** i zastosować technikę **One-Shot Learning** (pokazanie przykładu).

Oto sprawdzona konfiguracja promptów dla Twojego przypadku:

### 1\. System Message (Rola i Ograniczenia)

Tutaj definiujemy, że model jest maszyną do JSON-a, a nie czatbotem.

> **System Message:**
> "Jesteś automatem do ekstrakcji danych. Twoim zadaniem jest analiza notatek i zwracanie wyników **wyłącznie** w surowym formacie JSON. Nie używaj formatowania Markdown (\`\`\`json). Nie dodawaj żadnych komentarzy przed ani po kodzie JSON."

### 2\. User Message (Instrukcja + Przykład + Dane)

W wiadomości użytkownika musisz wyraźnie oddzielić instrukcję od danych wejściowych. Najlepiej użyć separatorów (np. `###`). Dodanie jednego przykładu (One-Shot) drastycznie zwiększa skuteczność mniejszych modeli.

> **User Message:**
>
> ```text
> ### INSTRUKCJA
> Przeanalizuj podaną notatkę pod kątem informacji o próbkach lub testerach produktów.
> ```

> ### WYMAGANY FORMAT
>
> Zwróć obiekt JSON z polami:
>
>   - "present": true (jeśli są informacje o próbkach/testerach) lub false (jeśli ich brak).
>   - "info": krótkie podsumowanie faktu o próbkach (np. "klient odebrał próbki") lub null (jeśli brak informacji).

> ### PRZYKŁAD (One-Shot)
>
> Input: "Spotkanie udane, klient prosił o cennik. Nie rozmawialiśmy o próbkach."
> Output: {"present": false, "info": null}

> ### NOTATKA DO ANALIZY
>
> "kontakt z klientem, podziękował za przesłane testery produktów. Jest zainteresowany współpracą"
>
> ```
> ```

-----

### Dlaczego to zadziała? (Kluczowe zmiany)

1.  **Mapowanie słów kluczowych:** W instrukcji dodałem "o próbkach lub **testerach**". Qwen jest bystry, ale przy 8B warto mu wprost powiedzieć, że "tester" to też "próbka" w tym kontekście.
2.  **Explicit JSON Constraint:** Fraza "Nie używaj formatowania Markdown" w System Message jest kluczowa. Modele często domyślnie pakują JSON w bloki kodu, co utrudnia parsowanie programistyczne.
3.  **Typy danych:** Zmieniłem `present: też` na `present: true` (boolean). Dla modelu językowego i późniejszego parsowania w kodzie (Python/JS) format `true/false` jest znacznie bardziej stabilny niż stringi "tak/nie".

### Opcja Zaawansowana (Structured Outputs)

Jeśli używasz Qwena przez API (np. vLLM, Ollama lub komercyjne API), wiele z nich obsługuje parametr `response_format` lub `json_mode`.

Jeśli używasz **Ollama**, możesz wymusić format w zapytaniu API:

```json
{
  "model": "qwen2.5:7b",
  "messages": [...],
  "format": "json",  <-- To jest kluczowe
  "stream": false
}
```

Jeśli korzystasz z biblioteki **Python** (np. Transformers/HuggingFace), upewnij się, że parsujesz output, ale powyższe prompty powinny dać Ci czysty string gotowy do `json.loads()`.

### Gotowy schemat dla Ciebie

Jeśli wkleisz to do Qwena:

**System:**
`Jesteś automatem do ekstrakcji danych. Zwracasz wyłącznie surowy JSON bez bloków markdown.`

**User:**
`Przeanalizuj tekst pod kątem wzmianek o próbkach/testerach. Format JSON: {"present": boolean, "info": string}. Tekst: "kontakt z klientem, podziękował za przesłane testery produktów. Jest zainteresowany współpracą"`

**Oczekiwana odpowiedź Qwen:**
`{"present": true, "info": "klient podziękował za przesłane testery produktów"}`

Czy chciałbyś, abym przygotował krótki skrypt w Pythonie, który automatycznie wysyła to zapytanie i parsuje odpowiedź?

-----------------------------------



Ollama posiada wbudowaną funkcję **`format: "json"`**, która jest absolutnym kluczem do sukcesu. Wymusza ona na modelu, aby generował **tylko i wyłącznie** poprawny JSON, nawet jeśli model "chciałby" coś dopowiedzieć.

Dzięki temu nie musisz walczyć z modelem w promptach aż tak agresywnie, ale nadal warto dobrze zdefiniować `System` i `User` message, aby zawartość tego JSON-a była trafna.

Oto kompletna konfiguracja.

### 1\. Definicja wiadomości (Prompty)

W Ollamie najlepiej rozdzielić to na rolę `system` (zachowanie) i `user` (dane).

#### System Message

Tu definiujemy format wyjściowy (schema).

> "Jesteś asystentem AI specjalizującym się w kategoryzacji danych CRM. Twoim zadaniem jest analiza notatki i ekstrakcja informacji w formacie JSON.
> Schemat JSON:
> {
> "present": boolean, // true jeśli w tekście jest mowa o próbkach/testerach, inaczej false
> "info": string // krótkie zdanie o tym co stało się z próbkami (np. "klient odebrał"), lub null jeśli brak
> }"

#### User Message

Tu podajemy tylko treść do analizy.

> "Notatka do analizy: kontakt z klientem, podziękował za przesłane testery produktów. Jest zainteresowany współpracą"

-----

### 2\. Jak wywołać żądanie (API / cURL)

Zakładając, że masz zainstalowany model `qwen2.5:7b` (najnowsza wersja 7B, często mylona z Qwen3), oto jak wygląda żądanie.

**Kluczowy parametr:** `"format": "json"`

#### Opcja A: Wywołanie przez terminal (cURL)

To najprostszy sposób na przetestowanie. Wklej to do terminala:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5:7b",
  "format": "json",
  "stream": false,
  "messages": [
    {
      "role": "system",
      "content": "Jesteś asystentem AI. Analizujesz tekst pod kątem wzmianek o próbkach lub testerach. Zwracasz TYLKO obiekt JSON o strukturze: {\"present\": boolean, \"info\": string}. Nie używaj markdown."
    },
    {
      "role": "user",
      "content": "Notatka: kontakt z klientem, podziękował za przesłane testery produktów. Jest zainteresowany współpracą"
    }
  ]
}'
```

#### Opcja B: Wywołanie w Pythonie (biblioteka `ollama` lub `requests`)

Jeśli budujesz aplikację, użyj tego kodu. Jest bardziej czytelny i od razu daje Ci obiekt w Pythonie.

```python
import requests
import json

url = "http://localhost:11434/api/chat"

payload = {
    "model": "qwen2.5:7b",  # Upewnij się, że masz tę nazwę (sprawdź: ollama list)
    "format": "json",       # <--- TO JEST NAJWAŻNIEJSZE
    "stream": False,
    "messages": [
        {
            "role": "system",
            "content": """
            Jesteś analitykiem CRM. Analizuj notatki pod kątem "próbek" lub "testerów".
            Wymagany format JSON:
            {
                "present": true/false,
                "info": "krótkie podsumowanie kontekstu próbek lub null"
            }
            """
        },
        {
            "role": "user",
            "content": "Notatka: kontakt z klientem, podziękował za przesłane testery produktów. Jest zainteresowany współpracą"
        }
    ]
}

response = requests.post(url, json=payload)
data = response.json()

# Wyciągnięcie treści
content_str = data['message']['content']
print(f"Surowa odpowiedź modelu: {content_str}")

# Parsowanie do słownika Python
result = json.loads(content_str)

if result['present']:
    print(f"Znaleziono próbki! Info: {result['info']}")
else:
    print("Brak próbek w notatce.")
```

### Dlaczego to zadziała lepiej?

1.  **Parametr `format: "json"`:** Ollama technicznie blokuje generowanie tokenów, które nie pasują do składni JSON (nawiasy klamrowe, cudzysłowy). Model *nie może* fizycznie napisać "Oto twoja odpowiedź:", bo to nie jest poprawny JSON.
2.  **Schema w System Prompt:** Wyjaśnienie modelowi, co dokładnie ma wpisać w pola (że `present` to `true/false`, a nie "też" lub "tak"), ułatwia mu "myślenie". Modele lepiej radzą sobie z wartościami logicznymi (`true`) niż z abstrakcyjnymi słowami.

Czy chcesz, abym pomógł Ci rozbudować ten JSON o dodatkowe pola (np. sentyment klienta)?

-------------------------------------------
Świetnie. Rozbudujmy ten model. Aby analiza była naprawdę użyteczna w CRM, warto dodać nie tylko sentyment, ale też np. **kategorię tematu** oraz flagę, czy wymagane jest **działanie następcze** (follow-up).

Dzięki temu Twoja aplikacja będzie mogła np. automatycznie kolorować notatki (sentyment) albo wrzucać je na listę "Do zrobienia" (follow-up).

Oto zaktualizowana konfiguracja dla Ollamy i Qwena.

### 1\. Nowy Schemat JSON

Zaprojektujmy strukturę tak, aby była czytelna. Informacje o próbkach zgrupujemy w podobiekcie `samples`.

```json
{
  "summary": "krótkie podsumowanie notatki w 3-5 słowach",
  "sentiment": "positive" | "neutral" | "negative",
  "category": "sprzedaż" | "reklamacja" | "spotkanie" | "inne",
  "follow_up_required": boolean, // czy trzeba coś z tym zrobić?
  "samples": {
    "present": boolean,
    "info": "szczegóły o próbkach lub null"
  }
}
```

### 2\. System Message (Instrukcja)

Tutaj kluczowe jest zdefiniowanie dozwolonych wartości dla sentymentu i kategorii, aby model nie wymyślał własnych (np. żeby zawsze pisał "positive", a nie "happy" czy "zadowolony").

**System Message:**

```text
Jesteś zaawansowanym asystentem CRM. Twoim zadaniem jest analiza notatki i ekstrakcja kluczowych metadanych do formatu JSON.

Przestrzegaj ściśle tego schematu:
1. "summary": Krótkie podsumowanie treści (maks 5 słów).
2. "sentiment": Określ wydźwięk notatki. Wybierz TYLKO jeden z: "positive", "neutral", "negative".
3. "category": Główny temat. Wybierz jeden z: "sprzedaż", "reklamacja", "spotkanie", "inne".
4. "follow_up_required": true jeśli notatka sugeruje konieczność podjęcia akcji (np. wysłanie oferty, kontakt), false jeśli to tylko informacja.
5. "samples": Obiekt zawierający analizę próbek/testerów:
    - "present": true jeśli wspomniano o próbkach/testerach.
    - "info": co się stało z próbkami (np. "klient odebrał") lub null.
```

### 3\. Kod Python (Gotowiec)

Oto kompletny kod, który wyśle zapytanie do Ollamy, odbierze rozbudowany JSON i wyświetli wyniki w czytelny sposób.

```python
import requests
import json

# Konfiguracja
url = "http://localhost:11434/api/chat"
model_name = "qwen2.5:7b" # Upewnij się, że masz tę wersję

# Notatka wejściowa (możesz tu wpisać cokolwiek)
user_note = "Klient dzwonił wściekły, bo testery dotarły uszkodzone. Oczekuje natychmiastowej wymiany. Poza tym pytał o nową ofertę."

# Definicja System Message
system_prompt = """
Jesteś analitykiem CRM. Analizuj tekst i zwróć JSON zgodny ze schematem:
{
  "summary": "string",
  "sentiment": "positive" | "neutral" | "negative",
  "category": "sprzedaż" | "reklamacja" | "spotkanie" | "inne",
  "follow_up_required": true | false,
  "samples": {
    "present": true | false,
    "info": "string lub null"
  }
}
"""

payload = {
    "model": model_name,
    "format": "json",       # Wymuszenie formatu JSON przez Ollamę
    "stream": False,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Notatka do analizy: {user_note}"}
    ]
}

try:
    print("Wysyłanie zapytania do Qwen...")
    response = requests.post(url, json=payload)
    response.raise_for_status() # Sprawdź czy nie ma błędu HTTP
    
    # Parsowanie
    response_json = response.json()
    content = response_json['message']['content']
    
    # Zamiana stringa JSON na obiekt Python (dict)
    data = json.loads(content)

    print("-" * 30)
    print(f"NOTATKA: {user_note}")
    print("-" * 30)
    print(f"Temat:      {data.get('summary')}")
    print(f"Kategoria:  {data.get('category').upper()}")
    print(f"Sentyment:  {data.get('sentiment')}")
    print(f"Wymaga działania?: {'TAK!' if data.get('follow_up_required') else 'Nie'}")
    
    if data['samples']['present']:
        print(f"Status próbek: {data['samples']['info']}")
    else:
        print("Status próbek: Brak wzmianki")
        
    print("-" * 30)
    # Wyświetlenie surowego JSON dla weryfikacji
    # print(json.dumps(data, indent=2))

except Exception as e:
    print(f"Wystąpił błąd: {e}")
```

### Czego się spodziewać (Wynik dla przykładowej notatki z kodu):

Dla notatki: *"Klient dzwonił wściekły, bo testery dotarły uszkodzone..."* Qwen powinien zwrócić coś w tym stylu:

  * **Sentyment:** `negative`
  * **Kategoria:** `reklamacja`
  * **Wymaga działania:** `true` (TAK\!)
  * **Próbki:** `true`, info: "testery dotarły uszkodzone"

### Wskazówka "Pro":

Jeśli zauważysz, że model czasem myli `category` (np. wpisuje "skarga" zamiast "reklamacja"), możesz w `System Message` dodać:
`"Używaj WYŁĄCZNIE podanych kategorii, nie wymyślaj nowych."`

Czy taki zestaw danych jest wystarczający, czy chcesz dodać jeszcze ekstrakcję konkretnych dat (np. "zadzwonię w przyszły wtorek")?
--------------------------------------------------------------



To świetne zastosowanie dla modelu 7B/8B. Kluczem do sukcesu przy kategoryzacji biznesowej, gdzie granice bywają płynne (np. różnica między "Planowaniem sprzedaży" a samą "Sprzedażą"), jest **dostarczenie modelowi definicji każdej kategorii**.

Model nie siedzi w Twojej głowie – musimy mu powiedzieć, co Ty rozumiesz przez "Pozyskiwanie".

Oto kompletne rozwiązanie: definicje, prompty i kod w Pythonie.

### 1\. Strategia: Zdefiniowanie Kategorii (Słownik)

Zanim wyślemy zapytanie, musimy ustalić, co oznaczają Twoje kategorie, aby Qwen się nie gubił. Użyjemy tego opisu w `System Message`.

  * **Pozyskiwanie:** Cold calling, leady, pierwszy kontakt, prospecting.
  * **Planowanie sprzedaży:** Prognozy, budżetowanie na przyszłe okresy, lejki sprzedażowe (pipeline).
  * **Sprzedaż:** Konkretne zamówienia, negocjacje cenowe, domykanie transakcji, oferta.
  * **Umowy:** Formalności, podpisy, RODO, aneksy, warunki prawne.
  * **Uwagi klienta:** Feedback o produkcie, skargi, sugestie zmian, opinie.
  * **Inne:** Sprawy administracyjne, towarzyskie, niepasujące do powyższych.

### 2\. System Prompt (Konfiguracja modelu)

Zaprojektujemy JSON tak, aby zwracał **kategorię główną** (do sortowania) oraz **listę tematów** (bo jedna notatka może dotyczyć i umowy, i uwag).

**System Message:**

```text
Jesteś ekspertem analizy CRM. Twoim zadaniem jest kategoryzacja notatek ze spotkań.
Dostępne kategorie:
1. "pozyskiwanie" (nowi klienci, leady, pierwszy kontakt)
2. "planowanie_sprzedazy" (prognozy, omawianie budżetów, pipeline)
3. "sprzedaz" (negocjacje, zamówienia, oferta, domykanie transakcji)
4. "umowy" (formalności, podpisy, aneksy, kwestie prawne)
5. "uwagi_klienta" (feedback, skargi, sugestie, opinie o produkcie)
6. "inne" (brak dopasowania)

Zwróć wynik w formacie JSON:
{
  "main_category": "jedna_kategoria_z_listy_powyzej",
  "tags": ["lista", "wszystkich", "pasujacych", "tematow"],
  "reasoning": "krótkie uzasadnienie wyboru w 1 zdaniu"
}
```

### 3\. Kod Python (Implementacja)

Ten skrypt wysyła notatkę, parsuje wynik i ładnie go wyświetla.

```python
import requests
import json

# --- KONFIGURACJA ---
URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b" # Użyj swojej wersji modelu

def categorize_crm_note(note_content):
    # Definicja zachowania modelu (System Prompt)
    system_instruction = """
    Jesteś analitykiem biznesowym. Przeanalizuj treść notatki i przypisz ją do kategorii.
    
    DEFINICJE KATEGORII:
    - "pozyskiwanie": poszukiwanie nowych klientów, pierwszy kontakt.
    - "planowanie_sprzedazy": rozmowy o przyszłych budżetach, strategii, potencjale.
    - "sprzedaz": bieżące zamówienia, negocjacje cen, wysłanie oferty.
    - "umowy": kwestie formalne, podpisywanie dokumentów, RODO.
    - "uwagi_klienta": opinie o produkcie, skargi, prośby o zmiany funkcjonalne.
    - "inne": tematy luźne lub niepasujące do powyższych.

    WYMAGANY FORMAT JSON:
    {
      "main_category": "string (wybierz najważniejszą kategorię)",
      "all_topics": ["string", "string"], (lista wszystkich pasujących kategorii)
      "key_points": ["string", "string"] (lista 2-3 kluczowych faktów z notatki)
    }
    """

    payload = {
        "model": MODEL,
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Treść notatki: {note_content}"}
        ]
    }

    try:
        response = requests.post(URL, json=payload)
        response.raise_for_status()
        
        # Parsowanie odpowiedzi
        result_json = response.json()['message']['content']
        return json.loads(result_json)
        
    except Exception as e:
        return {"error": str(e)}

# --- TESTOWANIE ---

# Przykładowe notatki (możesz dodać swoje)
test_notes = [
    "Spotkanie udane. Klient narzekał na długi czas dostawy, ale mimo to chce podpisać aneks przedłużający współpracę na rok.",
    "Zadzwoniłem do firmy X, nie byli zainteresowani, prosili o kontakt za kwartał. To był pierwszy kontakt.",
    "Omówiliśmy budżet na Q4. Planują zwiększyć zamówienia o 20%. Przesłałem cennik do akceptacji."
]

print(f"{'NOTATKA':<60} | {'KATEGORIA GŁÓWNA':<20}")
print("-" * 90)

for note in test_notes:
    data = categorize_crm_note(note)
    
    # Wyświetlanie wyników w konsoli
    if "error" not in data:
        # Skracanie notatki do wyświetlania
        short_note = (note[:55] + '..') if len(note) > 55 else note
        print(f"{short_note:<60} | {data.get('main_category', 'BŁĄD'):<20}")
        print(f"   -> Tematy: {data.get('all_topics')}")
        print(f"   -> Kluczowe: {data.get('key_points')}")
        print("-" * 90)
    else:
        print("Błąd przetwarzania:", data['error'])
```

### Analiza wyników (czego się spodziewać)

Dla powyższych notatek Qwen powinien zachować się następująco:

1.  **Notatka:** "Klient narzekał na czas dostawy... chce podpisać aneks..."

      * `main_category`: **umowy** (bo podpisanie aneksu jest decydujące) LUB **uwagi\_klienta** (zależy co model uzna za ważniejsze).
      * `all_topics`: ["uwagi\_klienta", "umowy"]

2.  **Notatka:** "Zadzwoniłem... pierwszy kontakt..."

      * `main_category`: **pozyskiwanie**

3.  **Notatka:** "Omówiliśmy budżet... zwiększyć zamówienia... przesłałem cennik"

      * `main_category`: **planowanie\_sprzedazy** (lub sprzedaż)
      * `all_topics`: ["planowanie\_sprzedazy", "sprzedaz"]

### Dlaczego dodałem pole `key_points`?

W systemach CRM samo "Kategoria: Sprzedaż" to często za mało. Dzięki polu `key_points`, qwen wyciągnie Ci "mięso" z notatki. W Twoim interfejsie będziesz mogła wyświetlić listę notatek w formie:

> **UMOWY** | 25.11.2023
>
>   * Podpisanie aneksu
>   * Skarga na czas dostawy

To znacznie przyspiesza przeglądanie historii klienta bez czytania pełnych tekstów ("ściany tekstu"). Czy to podejście pasuje do Twojego workflow?










-------------------------------




To idealne podejście. Przechodzimy od „co jest w notatce” (analiza treści) do „co mam z tym zrobić” (analiza akcyjna). Dla sprzedawcy kluczowe są **wyzwalacze (triggers)**: data kontaktu, zagrożenie ze strony konkurencji, lub "zamrażarka" (odłożenie w czasie).

Aby to osiągnąć, musimy zmienić strukturę JSON-a na taką, która przypomina **bilet zadania** w systemie CRM.

### Koncepcja: "Actionable Intelligence"

Zamiast tylko kategoryzować, poprosimy Qwena o wypełnienie pól, które sterują logiką aplikacji (np. ustawiają przypomnienie w kalendarzu lub zmieniają status leada na "Lost").

Oto zdefiniowane nowe pola:

1.  **`next_action`**: Co konkretnie trzeba zrobić (spotkanie, telefon, brak).
2.  **`scheduling_info`**: Kiedy to zrobić (wyciągnięcie daty/okresu np. "zima", "za tydzień").
3.  **`risk_alert`**: Czy klient wspomniał o konkurencji lub rezygnacji?
4.  **`lead_status`**: Czy proces jest aktywny, wstrzymany ("zamrażarka") czy utracony.

-----

### 1\. System Prompt (Wersja "Sales Productivity")

Musimy podać modelowi **dzisiejszą datę** w contextcie (w Pythonie), aby mógł poprawnie interpretować "w przyszły wtorek", choć przy modelach 7B bezpieczniej jest prosić o wyciągnięcie frazy czasowej, a datę obliczać w kodzie lub zostawić człowiekowi.

**Prompt Systemowy:**

```text
Jesteś asystentem sprzedaży AI. Twoim celem jest wyciągnięcie z notatki informacji niezbędnych do podjęcia dalszych działań (Actionable Items).

Zwróć wynik w formacie JSON zgodnym z poniższym schematem:

1. "main_topic": Kategoria ogólna (np. "sprzedaż", "negocjacje", "opieka").
2. "action_type": Co sprzedawca musi zrobić? Wybierz:
   - "schedule_meeting" (jeśli ustalono lub trzeba ustalić spotkanie)
   - "follow_up_call" (telefon kontrolny/przypominający)
   - "research" (sprawdzenie informacji/oferty)
   - "wait" (oczekiwanie, przesunięcie w czasie)
   - "none" (brak akcji, notatka informacyjna)
   - "recover" (próba odzyskania klienta od konkurencji)

3. "timing_extraction": Dokładny cytat z tekstu dotyczący terminu (np. "po nowym roku", "za 2 dni", "na zimę"). Jeśli brak - null.

4. "competitor_alert": true, jeśli klient wspomniał o konkurencji lub porównuje oferty. Inaczej false.

5. "lead_status_suggestion": Sugerowana zmiana statusu w CRM:
   - "hot" (klient gotowy do kupna)
   - "active" (proces trwa)
   - "deferred" (odłożone w czasie, np. "dzwonić zimą")
   - "lost_competitor" (wybrali konkurencję)
   - "churn_risk" (ryzyko odejścia)

6. "summary_for_list": Bardzo krótkie hasło na listę zadań (np. "Zadzwonić w listopadzie - konkurencja").
```

-----

### 2\. Kod Python (Z obsługą daty i wyzwalaczy)

Ten skrypt dynamicznie wstrzykuje dzisiejszą datę do promptu, co pomaga modelowi zrozumieć kontekst czasowy.

```python
import requests
import json
from datetime import datetime

# --- KONFIGURACJA ---
URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"

def analyze_sales_note(note_content):
    # Pobieramy dzisiejszą datę, by dać kontekst modelowi
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    system_instruction = f"""
    DZISIEJSZA DATA: {today_str}
    
    Jesteś asystentem CRM. Analizujesz notatki pod kątem produktywności sprzedawcy.
    Zwróć TYLKO JSON.
    
    SCHEMA JSON:
    {{
      "main_topic": "string",
      "action_type": "schedule_meeting" | "follow_up_call" | "wait" | "recover" | "none",
      "timing_extraction": "string lub null",
      "competitor_alert": boolean,
      "lead_status_suggestion": "hot" | "active" | "deferred" | "lost_competitor" | "churn_risk",
      "summary_for_list": "string (max 6 słów)"
    }}
    
    ZASADY:
    - Jeśli klient mówi "po nowym roku", "w zimę" -> lead_status_suggestion: "deferred", action_type: "wait".
    - Jeśli klient wybrał inną firmę -> lead_status_suggestion: "lost_competitor".
    - timing_extraction ma być cytatem z tekstu określającym kiedy ponowić kontakt.
    """

    payload = {
        "model": MODEL,
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Notatka: {note_content}"}
        ]
    }

    try:
        response = requests.post(URL, json=payload)
        response.raise_for_status()
        return json.loads(response.json()['message']['content'])
    except Exception as e:
        return {"error": str(e)}

# --- SCENARIUSZE TESTOWE (Symulacja życia sprzedawcy) ---

scenarios = [
    "Klient bardzo miły, ale powiedzieli, że budżet mają zamrożony do stycznia. Proszą o telefon w połowie zimy, wtedy wrócimy do rozmów.",
    "Niestety, zdecydowali się na rozwiązanie firmy ABC Consulting, bo było tańsze o 10%. Dziękują za ofertę.",
    "Spotkanie super. Chcą podpisać umowę w przyszły wtorek. Mam przygotować drafty.",
    "Mają wątpliwości czy nasz system obsłuży ich magazyn. Rozmawiają równolegle z firmą X. Trzeba przygotować porównanie funkcji."
]

print(f"{'ZADANIE (Summary)':<40} | {'STATUS':<15} | {'TERMIN':<20} | {'ALERT!'}")
print("-" * 95)

for note in scenarios:
    data = analyze_sales_note(note)
    
    if "error" not in data:
        # Formatowanie wyjścia
        summary = data.get('summary_for_list', '---')
        status = data.get('lead_status_suggestion', '---').upper()
        timing = data.get('timing_extraction') or "Brak terminu"
        
        # Oznaczenie alertu konkurencji
        alert = "!!! KONKURENCJA !!!" if data.get('competitor_alert') else ""
        
        # Wyświetlenie w tabeli
        print(f"{summary:<40} | {status:<15} | {timing:<20} | {alert}")
        
        # Opcjonalnie: logika biznesowa (co by zrobił system)
        # if data['action_type'] == 'wait':
        #     print(f"   >> SYSTEM: Ustawiam przypomnienie na: {timing}")
    else:
        print("Błąd:", data['error'])
```

### Analiza wyników (czego się spodziewać)

Po uruchomieniu tego kodu, model powinien zwrócić bardzo konkretne dane sterujące:

1.  **Dla notatki o "zamrożonym budżecie do stycznia":**

      * `action_type`: **wait** (lub follow\_up\_call)
      * `lead_status`: **DEFERRED** (to kluczowe dla managera sprzedaży)
      * `timing`: "w połowie zimy" / "do stycznia"
      * *System CRM może automatycznie ukryć tego leada do 1 stycznia.*

2.  **Dla notatki o "wyborze firmy ABC":**

      * `lead_status`: **LOST\_COMPETITOR**
      * `competitor_alert`: **true**
      * *System CRM może automatycznie zapytać o powód utraty.*

3.  **Dla notatki "Rozmawiają z firmą X, trzeba porównanie":**

      * `action_type`: **research** / **schedule\_meeting**
      * `lead_status`: **ACTIVE** (lub CHURN\_RISK zależy od tonu)
      * `competitor_alert`: **true**
      * `summary`: "Przygotować porównanie z firmą X"

### Jak to zintegrować z Twoją aplikacją?

Mając taki JSON, możesz zaprogramować prostą logikę w Pythonie:

  * `if competitor_alert == true`: Oznacz notatkę na czerwono 🔴.
  * `if action_type == "schedule_meeting"`: Wyświetl przycisk "Dodaj do Kalendarza Google" 📅.
  * `if lead_status == "deferred"`: Wyświetl przycisk "Uśpij na 30 dni" 💤.

To podejście sprawia, że AI nie jest tylko "katalogiem treści", ale aktywnie pomaga zarządzać czasem pracy sprzedawcy.