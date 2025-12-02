To jest "wisienka na torcie". Dzięki temu Twój system nie będzie wypluwał surowych kawałków tekstu z bazy, ale **udzieli płynnej, profesjonalnej odpowiedzi**, cytując źródła.

Musimy dodać krok **Syntezy (Synthesis)**.

### Dlaczego potrzebujemy zmiany w kodzie?

Twój obecny obiekt `llm` jest skonfigurowany z parametrem `format="json"`. To świetne do decydowania (Router), ale fatalne do pisania ładnych zdań.
Dlatego stworzymy drugą instancję modelu – nazwijmy ją **`llm_writer`** – która będzie "wolnym strzelcem" (bez wymuszonego JSONa) i zajmie się tylko pisaniem odpowiedzi.

Oto zaktualizowane fragmenty kodu do Twojego pliku `main.py`.

### 1\. Aktualizacja sekcji "Inicjalizacja Modeli"

Dodaj drugą instancję Qwena, dedykowaną do pisania tekstu.

```python
# --- ISTNIEJĄCY KOD ---
# Ten model służy do DECYZJI (zwraca JSON)
llm_router = ChatOllama(model=LLM_MODEL, temperature=0, format="json")

# --- NOWY KOD (DODAJ TO) ---
# Ten model służy do PISANIA ODPOWIEDZI (zwraca zwykły tekst)
# Temperature 0.3 daje mu odrobinę kreatywności, żeby zdania brzmiały naturalnie
llm_writer = ChatOllama(model=LLM_MODEL, temperature=0.3)
```

### 2\. Nowa funkcja: Synteza RAG

Dodaj tę funkcję w sekcji `FUNKCJE LOGICZNE`. Ona bierze "surowe mięso" (wyniki z bazy) i smaży z nich "gotowe danie" (odpowiedź).

```python
def synthesize_answer(user_query: str, retrieved_docs: List[Dict]):
    """
    Tworzy ładną odpowiedź na podstawie znalezionych dokumentów.
    """
    # 1. Sklejamy treść znalezionych dokumentów w jeden tekst
    context_text = "\n\n---\n\n".join([doc['content'] for doc in retrieved_docs])
    
    # 2. Prompt dla Pisarza
    rag_prompt = f"""
    Jesteś pomocnym asystentem korporacyjnym.
    Odpowiedz na pytanie użytkownika WYŁĄCZNIE na podstawie poniższych fragmentów dokumentacji.
    
    FRAGMENTY DOKUMENTACJI:
    {context_text}
    
    PYTANIE UŻYTKOWNIKA: 
    {user_query}
    
    INSTRUKCJE:
    - Jeśli odpowiedź jest w dokumencie, napisz ją zwięźle i profesjonalnie.
    - Jeśli informacji NIE MA w fragmentach, napisz: "Niestety, w bazie wiedzy nie znalazłem informacji na ten temat."
    - Nie wymyślaj faktów spoza podanego tekstu.
    """
    
    # 3. Wywołanie modelu piszącego
    response = llm_writer.invoke([HumanMessage(content=rag_prompt)])
    
    return response.content
```

### 3\. Aktualizacja Endpointu (`handle_query`)

Podmieniamy logikę w bloku `elif tool_name == "search_knowledge_base":`.

```python
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    # ... (kod routera bez zmian, używamy llm_router) ...
    
    # ... wewnątrz if/else ...

    elif tool_name == "search_knowledge_base":
        # A. Pobieramy parametry
        search_query = params.get("search_query")
        
        # B. Szukamy w bazie (Postgres + Vector)
        # Pobieramy np. 3 najlepsze fragmenty, żeby dać modelowi szerszy kontekst
        raw_results = execute_vector_search(search_query) 
        
        if not raw_results:
            return QueryResponse(
                answer="Przeszukałem bazę wiedzy, ale nie znalazłem pasujących dokumentów.",
                tool_used=tool_name,
                data=[]
            )

        # C. SYNTEZA (To jest ten nowy krok!)
        # Wysyłamy pytanie i znalezione fragmenty do llm_writer
        final_polished_answer = synthesize_answer(request.query, raw_results)
        
        return QueryResponse(
            answer=final_polished_answer, 
            tool_used=tool_name, 
            data=raw_results # Zwracamy też surowe dane, żebyś widział, skąd wziął info (do debugowania)
        )
```

### Jak to teraz zadziała? (Flow)

1.  **User:** *"Jaka jest procedura reklamacji pompy?"*
2.  **Router (JSON):** Wybiera `search_knowledge_base` z parametrem `reklamacja pompy`.
3.  **Postgres:** Znajduje w bazie fragment PDFa: *"Zwroty pomp hydraulicznych wymagają formularza Z-12..."*.
4.  **Synthesizer (Writer):** Dostaje ten fragment i pytanie.
5.  **Wynik:**
    > "Zgodnie z procedurą, reklamacja pompy hydraulicznej wymaga wypełnienia formularza Z-12. Dokument należy przesłać do działu jakości w ciągu 14 dni."

### Co zyskałeś?

  * **Profesjonalizm:** Użytkownik nie dostaje "surowego wyniku SQL", tylko pełne zdanie.
  * **Weryfikacja:** Jeśli baza zwróci głupoty (np. fragment o urlopach zamiast o pompach, bo słowa były podobne), LLM w fazie syntezy oceni: *"W podanym kontekście nie widzę odpowiedzi na Twoje pytanie"* (zgodnie z instrukcją w prompcie). To dodatkowa warstwa ochrony przed halucynacjami.


  

To doskonała decyzja. Zastosowanie **Chain-of-Thought (CoT)** w połączeniu z wymuszonym formatem JSON to obecnie najstabilniejsza metoda sterowania modelami open-source (takimi jak Qwen czy Llama 3) w architekturze agentowej.

Model nie "zgaduje" od razu funkcji. Zmuszamy go, by najpierw **"pomyślał"** (wygenerował pole `thought`), a dopiero potem podjął decyzję. To drastycznie redukuje błędy logiczne.

Oto zaktualizowany, kompletny kod `main.py`, który wdraża te "Best Practices".

### Co zmieniamy? (Kluczowe ulepszenia)

1.  **Rezygnacja z `bind_tools`:** Narzędzia definiujemy w Prompcie Systemowym.
2.  **Pole `thought`:** Wymuszamy na modelu analizę przed akcją.
3.  **Dwa mózgi:**
      * `llm_router` (Temp=0, JSON): Bezwzględny logik do routingu.
      * `llm_writer` (Temp=0.3, Text): Kreatywny asystent do pisania odpowiedzi końcowej.
4.  **Centralny Dispatcher:** Czytelna instrukcja `if/elif` w Pythonie zamiast magii bibliotecznej.

### Kod Aplikacji (`main.py`)

```python
import json
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

# --- 1. KONFIGURACJA ---
DB_CONFIG = "dbname=knowledge_base user=admin password=SecretPassword123! host=localhost"
LLM_MODEL = "qwen2.5:7b"
EMBED_MODEL = "nomic-embed-text"

app = FastAPI(title="Corporate Agent (CoT Edition)")

# Mózg 1: ROUTER (Logika, precyzja, JSON)
llm_router = ChatOllama(model=LLM_MODEL, temperature=0, format="json")

# Mózg 2: WRITER (Synteza, język naturalny)
llm_writer = ChatOllama(model=LLM_MODEL, temperature=0.3)

# Model Embeddings (do wektoryzacji zapytań)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

# --- 2. DEFINICJA NARZĘDZI (SCHEMA DLA PROMPTU) ---
# To jest "Menu" dla naszego AI. Musi być czytelne.
TOOLS_SCHEMA = [
    {
        "name": "check_product_availability",
        "description": "Sprawdza ilościowe stany magazynowe produktów.",
        "parameters": {
            "product_query": "Nazwa produktu lub kod SKU (np. 'pompa X500')",
            "location": "Opcjonalnie: magazyn lub kraj (np. 'Brazylia')"
        }
    },
    {
        "name": "get_client_snapshot",
        "description": "Pobiera dane o kliencie: status, opiekun, adres, NIP.",
        "parameters": {
            "client_name": "Nazwa firmy (np. 'Embraer')"
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Przeszukuje dokumenty, procedury, regulaminy i wiedzę miękką.",
        "parameters": {
            "search_query": "Fraza do wyszukania semantycznego (np. 'procedura zwrotu')"
        }
    }
]

# --- 3. SYSTEM PROMPT (Chain-of-Thought) ---
ROUTER_PROMPT = f"""
Jesteś inteligentnym koordynatorem systemu korporacyjnego.
Twoim celem jest zrozumienie intencji użytkownika i wybranie odpowiedniego narzędzia.

DOSTĘPNE NARZĘDZIA:
{json.dumps(TOOLS_SCHEMA, indent=2, ensure_ascii=False)}

INSTRUKCJA FORMATU WYJŚCIOWEGO (JSON):
Musisz zwrócić obiekt JSON o następującej strukturze. Klucz "thought" jest najważniejszy - opisz w nim swój tok rozumowania.

{{
  "thought": "Tutaj wpisz analizę: Czego szuka użytkownik? Czy to dane liczbowe (SQL) czy wiedza (Wektor)? Które narzędzie pasuje najlepiej?",
  "tool_name": "nazwa_wybranego_narzędzia" LUB null (jeśli to zwykła rozmowa),
  "parameters": {{
    "nazwa_parametru": "wartość wyciągnięta z pytania"
  }},
  "response": "Tekst odpowiedzi TYLKO w przypadku, gdy tool_name to null (np. przywitanie lub prośba o doprecyzowanie)"
}}

Przykład:
User: "Ile mamy pomp w Brazylii?"
JSON:
{{
  "thought": "Użytkownik pyta o ilość (stan magazynowy) konkretnego produktu w konkretnej lokalizacji. Użyję narzędzia check_product_availability.",
  "tool_name": "check_product_availability",
  "parameters": {{ "product_query": "pompa", "location": "Brazylia" }}
}}
"""

# --- 4. MODELE DANYCH (API) ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    final_answer: str
    thought_process: str  # Żebyś widział, co AI myśli (do debugowania)
    tool_used: Optional[str] = None
    raw_data: Optional[Any] = None

# --- 5. IMPLEMENTACJA FUNKCJI (BACKEND) ---

def execute_sql_stock(product: str, location: str = None):
    """Symulacja zapytania SQL"""
    # Tu wpinasz prawdziwy: SELECT sum(qty) FROM stock WHERE ...
    return {"product": product, "location": location or "Global", "qty": 142, "status": "In Stock"}

def execute_sql_client(client_name: str):
    """Symulacja zapytania SQL"""
    return {"client": client_name, "segment": "VIP", "manager": "Jan Kowalski", "debt": 0}

def execute_vector_search(query_text: str):
    """Prawdziwe wyszukiwanie PGVECTOR"""
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()
    try:
        query_vector = embeddings.embed_query(query_text)
        # Szukamy w notatkach i produktach (można rozdzielić)
        sql = """
            SELECT content, 1 - (embedding <=> %s::vector) as similarity
            FROM sales_notes
            WHERE 1 - (embedding <=> %s::vector) > 0.5  -- Próg trafności
            ORDER BY embedding <=> %s::vector LIMIT 3;
        """
        cur.execute(sql, (query_vector, query_vector, query_vector))
        results = [{"content": r[0], "score": float(r[1])} for r in cur.fetchall()]
        return results
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        conn.close()

def synthesize_rag_response(user_query: str, context_data: Any) -> str:
    """Drugi model (Writer) układa odpowiedź"""
    prompt = f"""
    Na podstawie dostarczonych danych odpowiedz na pytanie użytkownika.
    
    DANE/KONTEKST:
    {json.dumps(context_data, ensure_ascii=False)}
    
    PYTANIE: {user_query}
    
    Zasady:
    1. Bądź konkretny i profesjonalny.
    2. Jeśli dane to tabela/liczby, przedstaw je czytelnie.
    3. Jeśli dane to fragmenty tekstu, streść najważniejsze informacje.
    """
    response = llm_writer.invoke([HumanMessage(content=prompt)])
    return response.content

# --- 6. GŁÓWNY ENDPOINT (ROUTER) ---

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    print(f"\n[USER QUERY]: {request.query}")
    
    # KROK A: DECYZJA (CoT)
    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=request.query)
    ]
    
    # Router zwraca JSON
    router_response = llm_router.invoke(messages)
    
    try:
        decision = json.loads(router_response.content)
    except json.JSONDecodeError:
        # Fallback, gdyby model zwariował (rzadkie przy format="json")
        return QueryResponse(
            final_answer="Przepraszam, wystąpił błąd analizy zapytania.",
            thought_process="JSON Decode Error"
        )

    thought = decision.get("thought", "Brak procesu myślowego")
    tool_name = decision.get("tool_name")
    params = decision.get("parameters", {})
    
    print(f"[AI THOUGHT]: {thought}")
    print(f"[AI TOOL]: {tool_name} | Params: {params}")

    # KROK B: WYKONANIE (DISPATCHER)
    data_result = None
    
    if tool_name == "check_product_availability":
        data_result = execute_sql_stock(
            product=params.get("product_query"), 
            location=params.get("location")
        )
        
    elif tool_name == "get_client_snapshot":
        data_result = execute_sql_client(
            client_name=params.get("client_name")
        )
        
    elif tool_name == "search_knowledge_base":
        data_result = execute_vector_search(
            query_text=params.get("search_query")
        )

    elif tool_name is None:
        # Zwykła rozmowa (Chit-Chat)
        return QueryResponse(
            final_answer=decision.get("response", "Słucham?"),
            thought_process=thought
        )
    
    else:
        return QueryResponse(
            final_answer=f"Nieznane narzędzie: {tool_name}",
            thought_process=thought
        )

    # KROK C: SYNTEZA ODPOWIEDZI
    # Niezależnie czy to SQL czy Wektor - niech Writer ubierze to w ładne słowa
    final_text = synthesize_rag_response(request.query, data_result)

    return QueryResponse(
        final_answer=final_text,
        thought_process=thought,
        tool_used=tool_name,
        raw_data=data_result
    )

# Uruchomienie: uvicorn main:app --reload
```

### Dlaczego to rozwiązanie jest "Kuloodporne"?

1.  **Debugowalność:** Endpoint zwraca pole `thought_process`. Dzięki temu w aplikacji (lub w logach) dokładnie widzisz, *dlaczego* model wybrał taką funkcję.
      * *Przykład:* "Myślałem, że user pyta o procedurę, ale użył słowa 'ilość', więc zmieniam na check\_stock".
2.  **Uniwersalna Synteza:** Zauważ, że wynik funkcji SQL (`data_result`) też przepuszczamy przez `synthesize_rag_response`.
      * Dzięki temu, zamiast suchego JSONa `{"qty": 142}`, użytkownik dostanie: *"Obecnie w magazynie mamy 142 sztuki tego produktu, status dostępny."*
3.  **Bezpieczeństwo typów:** Jeśli model zwróci błędny parametr (np. liczbę zamiast stringa), Twój kod Pythona wewnątrz funkcji (`execute_sql...`) może to łatwo wyłapać i obsłużyć, zanim cokolwiek trafi do bazy.

To jest architektura gotowa na produkcję (Production-Grade MVP).


Rozumiem problem. Biblioteki wysokiego poziomu (jak `langchain_ollama`) często "magicznie" doklejają końcówki do URL-i, co przy niestandardowych proxy lub tunelach (gdzie `base_url` zawiera już pełną ścieżkę) powoduje błędy typu 404.

W takim przypadku musimy zejść poziom niżej i użyć biblioteki **`requests`** w Pythonie, aby mieć 100% kontroli nad tym, gdzie i co wysyłamy.

Oto kompletne rozwiązanie przepisane na **surowe żądania HTTP (Raw Requests)**, eliminujące `ChatOllama`. Zachowujemy logikę *Chain-of-Thought* i architekturę routera.

### Zmiany w architekturze:

1.  **Brak `ChatOllama`:** Zastępujemy go funkcją `call_ollama_api`.
2.  **Ręczna obsługa wiadomości:** Zamiast obiektów `SystemMessage`, używamy słowników `{"role": "system", "content": "..."}` wymaganych przez API Ollamy.
3.  **Embeddings:** Również przepisane na `requests`, abyś miał kontrolę nad endpointem `/api/embeddings`.

### Plik `main.py`

```python
import json
import requests
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, List, Dict

# --- 1. KONFIGURACJA SIECIOWA (Pełna kontrola) ---
# Tutaj wpisz swój PEŁNY adres. Skoro mówisz, że Twój base_url ma już /api/chat:
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"  
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings" 

# Modele
LLM_MODEL = "qwen2.5:7b"
EMBED_MODEL = "nomic-embed-text"

# Baza Danych
DB_CONFIG = "dbname=knowledge_base user=admin password=SecretPassword123! host=localhost"

app = FastAPI(title="Corporate Agent (Raw Requests Edition)")

# --- 2. KLIENT HTTP DO OLLAMY (Zastępuje LangChain ChatOllama) ---

def call_ollama_api(messages: List[Dict], temperature: float = 0, json_mode: bool = False) -> str:
    """
    Wysyła surowe żądanie POST do Twojego endpointu.
    """
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False # Dla API łatwiej obsłużyć brak streamingu
    }
    
    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=30)
        response.raise_for_status() # Rzuci błąd jeśli kod != 200
        
        # Ollama zwraca strukturę: {"message": {"content": "..."}}
        return response.json()["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        print(f"Błąd połączenia z Ollama: {e}")
        # W razie awarii zwracamy pusty JSON lub tekst błędu
        return "{}" if json_mode else "Błąd modelu AI."

def get_embedding_raw(text: str) -> List[float]:
    """
    Wysyła żądanie o wektor (zastępuje OllamaEmbeddings).
    """
    payload = {
        "model": EMBED_MODEL,
        "prompt": text
    }
    try:
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Błąd embeddingu: {e}")
        return []

# --- 3. DEFINICJE I PROMPTY ---

TOOLS_SCHEMA = [
    {
        "name": "check_product_availability",
        "description": "Sprawdza stany magazynowe.",
        "parameters": {"product_query": "Nazwa/kod produktu", "location": "Opcjonalnie: kraj/magazyn"}
    },
    {
        "name": "search_knowledge_base",
        "description": "Szuka w dokumentacji i procedurach (Semantic Search).",
        "parameters": {"search_query": "Fraza do wyszukania"}
    }
]

ROUTER_SYSTEM_PROMPT = f"""
Jesteś systemem decyzyjnym. Twoim zadaniem jest wybranie narzędzia.

DOSTĘPNE NARZĘDZIA:
{json.dumps(TOOLS_SCHEMA, ensure_ascii=False)}

Zwróć ODPOWIEDŹ TYLKO W FORMACIE JSON:
{{
  "thought": "Opisz swój proces myślowy",
  "tool_name": "nazwa_funkcji" lub null,
  "parameters": {{ "param1": "val1" }},
  "response": "Tekst dla użytkownika (tylko gdy tool_name to null)"
}}
"""

# --- 4. LOGIKA BIZNESOWA (Funkcje) ---

def execute_sql_stock(product: str, location: str = None):
    # Symulacja SQL
    return {"product": product, "location": location or "Global", "qty": 88, "status": "Available"}

def execute_vector_search(query_text: str):
    # 1. Pobieramy wektor (RAW REQUEST)
    query_vector = get_embedding_raw(query_text)
    
    if not query_vector:
        return [{"error": "Nie udało się wygenerować wektora."}]

    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()
    try:
        # 2. Szukamy w bazie
        sql = """
            SELECT content, 1 - (embedding <=> %s::vector) as similarity
            FROM sales_notes
            WHERE 1 - (embedding <=> %s::vector) > 0.4
            ORDER BY embedding <=> %s::vector LIMIT 3;
        """
        cur.execute(sql, (query_vector, query_vector, query_vector))
        results = [{"content": r[0], "score": float(r[1])} for r in cur.fetchall()]
        return results
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        conn.close()

# --- 5. MODELE API ---

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    final_answer: str
    thought_process: str
    tool_used: Optional[str] = None
    raw_data: Optional[Any] = None

# --- 6. ENDPOINT GŁÓWNY ---

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    print(f"\n[USER]: {request.query}")
    
    # --- FAZA 1: ROUTER (Mózg Logiczny) ---
    # Budujemy listę wiadomości ręcznie (zamiast HumanMessage)
    router_messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": request.query}
    ]
    
    # Wywołanie API z wymuszeniem JSON
    raw_response = call_ollama_api(router_messages, temperature=0, json_mode=True)
    
    try:
        decision = json.loads(raw_response)
    except json.JSONDecodeError:
        return QueryResponse(final_answer="Błąd modelu (zły format JSON).", thought_process=raw_response)

    thought = decision.get("thought", "")
    tool_name = decision.get("tool_name")
    params = decision.get("parameters", {})
    
    print(f"[THOUGHT]: {thought}")
    print(f"[TOOL]: {tool_name}")

    # --- FAZA 2: WYKONANIE (Dispatcher) ---
    data_result = None
    
    if tool_name == "check_product_availability":
        data_result = execute_sql_stock(params.get("product_query"), params.get("location"))
        
    elif tool_name == "search_knowledge_base":
        data_result = execute_vector_search(params.get("search_query"))
        
    elif tool_name is None:
        return QueryResponse(final_answer=decision.get("response", "Słucham?"), thought_process=thought)

    # --- FAZA 3: SYNTEZA (Writer) ---
    # Prompt dla pisarza
    writer_system_prompt = "Jesteś asystentem. Odpowiedz na pytanie użytkownika na podstawie podanych danych."
    writer_user_content = f"Pytanie: {request.query}\n\nDane z systemu: {json.dumps(data_result, ensure_ascii=False)}"
    
    writer_messages = [
        {"role": "system", "content": writer_system_prompt},
        {"role": "user", "content": writer_user_content}
    ]
    
    # Wywołanie API w trybie tekstowym (bez format="json") i z wyższą temperaturą
    final_text = call_ollama_api(writer_messages, temperature=0.3, json_mode=False)

    return QueryResponse(
        final_answer=final_text,
        thought_process=thought,
        tool_used=tool_name,
        raw_data=data_result
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Kluczowe różnice w tym podejściu:

1.  **Funkcja `call_ollama_api`:** To jest Twój nowy "silnik".
      * Przyjmuje `messages` jako zwykłą listę słowników.
      * Wysyła `POST` dokładnie tam, gdzie zdefiniujesz w `OLLAMA_CHAT_URL`. Nie dokleja nic magicznie.
      * Parametr `json_mode=True` dodaje `"format": "json"` do payloadu, co jest kluczowe dla Routera (Qwen).
2.  **Embeddings:** Funkcja `get_embedding_raw` robi to samo dla wektorów. Zwróć uwagę na `OLLAMA_EMBED_URL`. Jeśli Twój adres to np. `http://moj-serwer/v1/api/chat`, to embeddingi prawdopodobnie są pod `http://moj-serwer/v1/api/embeddings`. Dostosuj tę zmienną na górze pliku.
3.  **Lekkość:** Nie instalujesz całego frameworka LangChain, jeśli potrzebujesz tylko prostego requestu. Kod jest bardziej przejrzysty i łatwiejszy do debugowania (widzisz dokładnie, jaki JSON leci do Ollamy).