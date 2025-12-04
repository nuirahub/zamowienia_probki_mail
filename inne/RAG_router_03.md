You are the Router Agent for a RAG-based sales support system. Your only job is to analyze the user's input (in Polish) and select the single best tool to retrieve the necessary information.

You have access to the following two tools:

1. TOOL NAME: "sql_db"
   - DESCRIPTION: Use this for structured, factual data that resides in rows and columns.
   - CAPABILITIES: retrieving phone numbers, email addresses, NIP numbers, addresses, product prices, stock levels, list of orders, dates of last order, total spending sums, specific product categories.
   - KEYWORDS: "ile", "kiedy", "cena", "numer", "adres", "lista produktów", "zamówienia", "wartość".

2. TOOL NAME: "vector_search"
   - DESCRIPTION: Use this for unstructured text data, qualitative analysis, and context.
   - CAPABILITIES: retrieving meeting summaries, client sentiment, history of conversations, future plans, "Next Steps", details about personal relationships, specific problems mentioned in conversation, objections.
   - KEYWORDS: "podsumuj", "o czym", "nastroje", "plany", "problem", "relacja", "opinia".

INSTRUCTIONS:
1. Analyze the user's input step-by-step.
2. Determine which tool is best suited to answer. Do not use both; pick the primary one.
3. Extract necessary parameters.
4. If the user asks about something completely unrelated to sales/CRM (e.g., weather, general knowledge), or if the intent is unclear, use the tool name "no_tool".

OUTPUT FORMAT:
You must output a SINGLE JSON object containing the following keys:
- "thinking": A brief explanation of your reasoning process (Chain of Thought).
- "tool_name": The exact name of the tool selected ("sql_db", "vector_search", or "no_tool").
- "parameters": A dictionary of parameters extracted from the query. For each parameter, include "value" and "is_required" (boolean).
- "justification": A short sentence explaining why this tool was chosen.

EXAMPLES:

User: "Jaki jest numer telefonu do firmy ABC?"
Output:
{
  "thinking": "The user is asking for specific contact data (phone number). This is structured data stored in the client database.",
  "tool_name": "sql_db",
  "parameters": {
    "client_name": {"value": "ABC", "is_required": true},
    "info_type": {"value": "phone_number", "is_required": true}
  },
  "justification": "Phone numbers are structured fields in the SQL database."
}

User: "Czy klient X był zadowolony z ostatniego spotkania?"
Output:
{
  "thinking": "The user asks about sentiment/satisfaction ('zadowolony'). This requires analyzing text notes from the meeting.",
  "tool_name": "vector_search",
  "parameters": {
    "client_name": {"value": "X", "is_required": true},
    "topic": {"value": "sentiment", "is_required": false}
  },
  "justification": "Sentiment and meeting satisfaction are qualitative data found in meeting notes."
}

User: "Opowiedz mi bajkę o robotach."
Output:
{
  "thinking": "The request is creative writing and unrelated to CRM data.",
  "tool_name": "no_tool",
  "parameters": {},
  "justification": "brak wyników w bazie wiedzy"
}

User: "Ile wydaliśmy na produkt Y w zeszłym roku?"
Output:
{
  "thinking": "The user asks for a financial sum ('ile wydaliśmy') associated with a product and a timeframe. This is a calculation on structured order data.",
  "tool_name": "sql_db",
  "parameters": {
    "product_name": {"value": "Y", "is_required": true},
    "timeframe": {"value": "last year", "is_required": true}
  },
  "justification": "Financial sums and order history are stored in the SQL database."
}

Now, handle the following user input. Output ONLY the JSON object.



-----------------------


Dlaczego ten prompt zadziała lepiej z Qwen 3/2.5?
Thinking Key: Pole thinking wymusza na modelu Chain of Thought. Zanim model poda nazwę narzędzia, musi "na głos" przeanalizować pytanie. To drastycznie zmniejsza liczbę błędnych klasyfikacji w mniejszych modelach.

Jasne definicje: Rozdzieliłem narzędzia nie tylko opisem, ale też konkretnymi słowami kluczowymi (KEYWORDS). Qwen bardzo dobrze reaguje na takie mapowanie słów.

Strict JSON: Modele 7B-8B świetnie radzą sobie z JSONem, jeśli dostaną 3-4 przykłady (Few-Shot). W przykładach zawarłem skrajne przypadki (SQL, Vector, Bzdura).

Flaga is_required: Dodałem to do parametrów, o co prosiłaś. Pozwala to w dalszej części kodu sprawdzić, czy masz wszystkie dane (np. jeśli user zapyta "Jaka jest cena?" bez podania produktu, sql_tool zwróci product_name: null, is_required: true, co pozwoli Twojemu systemowi dopytać użytkownika: "O jaki produkt chodzi?").

Obsługa błędu "no_tool"
W kodzie Pythona musisz obsłużyć wynik no_tool:

Python

if result['tool_name'] == 'no_tool':
    print("System: Przepraszam, ale brak wyników w bazie wiedzy dla tego zapytania.")
elif result['tool_name'] == 'sql_db':
    # uruchom agenta SQL
    pass
elif result['tool_name'] == 'vector_search':
    # uruchom RAG na dokumentach
    pass

-----------------------------------------------

Dlaczego?

Walidacja: Jeśli model wypluje coś, co nie pasuje do schematu (np. brak pola "thinking"), Pydantic to odrzuci lub (z odpowiednim parserem) poprosi model o poprawkę (RetryParser).

Typowanie: Dostajesz gotowy obiekt Python, a nie string, którego trzeba parsować json.loads().

Opisy w Field: To, co wpiszesz w Field(description="..."), staje się częścią promptu dla modelu. To najskuteczniejszy sposób instruktażu.

Oto jak wdrożyć Twój Router, używając PydanticOutputParser w LangChain. To rozwiązanie jest kompatybilne z Twoim podejściem (CoT + brak bind_tools).

1. Definicja Modeli Pydantic
Zdefiniujmy strukturę. Użyjemy Enum dla nazw narzędzi, aby model nie wymyślał własnych nazw (np. "sql_tool" zamiast "sql_db").

Python

from typing import List, Optional
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from enum import Enum

# 1. Definiujemy dozwolone narzędzia jako Enum (maksymalna precyzja)
class ToolName(str, Enum):
    SQL_DB = "sql_db"
    VECTOR_SEARCH = "vector_search"
    NO_TOOL = "no_tool"

# 2. Definicja pojedynczego parametru
class Parameter(BaseModel):
    name: str = Field(description="Nazwa parametru, np. 'client_name', 'date', 'product_id'")
    value: str = Field(description="Wyekstrahowana wartość parametru z zapytania")
    is_required: bool = Field(description="Czy ten parametr jest niezbędny do wykonania zapytania?")

# 3. Główny obiekt odpowiedzi (Router)
class RouterResponse(BaseModel):
    # Ważne: 'thinking' dajemy na początku. Model najpierw "pomyśli", co zwiększy trafność wyboru narzędzia.
    thinking: str = Field(description="Krótki proces myślowy (Chain of Thought). Wyjaśnij krok po kroku, dlaczego wybierasz to narzędzie.")
    
    tool_name: ToolName = Field(description="Wybierz jedno narzędzie najlepiej pasujące do zapytania.")
    
    parameters: List[Parameter] = Field(description="Lista parametrów wyciągniętych z pytania.", default=[])
    
    justification: str = Field(description="Jedno zdanie podsumowujące decyzję.")

    # Opcjonalnie: Walidator logiczny (np. sprawdzenie czy SQL ma parametry)
    @validator('parameters')
    def validate_sql_has_params(cls, v, values):
        # Dostęp do tool_name jest w values, ale w Pydantic v1 bywa tricky przed walidacją całości.
        # To miejsce na zaawansowaną logikę, jeśli potrzebujesz.
        return v
2. Implementacja w LangChain (Prompt + Parser)
Teraz łączymy to z Twoim modelem Qwen. Kluczem jest parser.get_format_instructions(), który automatycznie wygeneruje instrukcję JSON dla modelu na podstawie powyższych klas.

Python

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.llms import Ollama # Zakładam Ollamę, dostosuj import pod siebie

# Inicjalizacja modelu
llm = Ollama(model="qwen2.5:7b", temperature=0)

# Inicjalizacja parsera
parser = PydanticOutputParser(pydantic_object=RouterResponse)

# Prompt
router_prompt_template = """
You are an expert Router Agent for a sales RAG system. Your goal is to route the user question to the correct data source.

DATA SOURCES:
1. "sql_db": Structured data (orders, product prices, client contact info, stock levels, sales sums).
   - Use for: "How much", "When", "Price of", "Phone number", "Address", "List orders".
2. "vector_search": Unstructured data (meeting notes, emails, sentiment, context, history of relations).
   - Use for: "Summarize", "Client mood", "What did we talk about", "Problems", "Future plans".
3. "no_tool": General chit-chat or questions unrelated to the business data.

INSTRUCTIONS:
1. Analyze the user input carefully.
2. Fill the "thinking" field first to reason about the user intent.
3. Select the strictly correct tool from the allowed list.
4. Extract key parameters needed for the query.

{format_instructions}

USER INPUT: {question}
"""

prompt = PromptTemplate(
    template=router_prompt_template,
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Łańcuch
chain = prompt | llm | parser

# --- TESTOWANIE ---

# Przykład 1: SQL
query1 = "Jaka jest cena produktu X i ile go mamy na stanie?"
try:
    result1 = chain.invoke({"question": query1})
    print(f"--- Pytanie: {query1} ---")
    print(f"Narzędzie: {result1.tool_name}")
    print(f"Myślenie: {result1.thinking}")
    print(f"Parametry: {result1.parameters}")
except Exception as e:
    print(f"Błąd parsowania: {e}")

# Przykład 2: Wektor
print("\n")
query2 = "Czy klient Acme Corp był zadowolony z ostatniego spotkania?"
try:
    result2 = chain.invoke({"question": query2})
    print(f"--- Pytanie: {query2} ---")
    print(f"Narzędzie: {result2.tool_name}")
    print(f"Myślenie: {result2.thinking}")
except Exception as e:
    print(f"Błąd parsowania: {e}")
Dlaczego to działa lepiej dla Ciebie?
Wymuszone "Thinking": W definicji RouterResponse pole thinking jest pierwsze. Model, generując JSON, zacznie od: {"thinking": "User asks about price...". To klasyczny CoT, który poprawia jakość wyboru w kolejnym polu tool_name.

Enum ToolName: Jeśli model spróbuje wstawić "database_tool" (coś, co zmyślił), Pydantic wyrzuci błąd walidacji, zanim kod pójdzie dalej. To Twoja bariera bezpieczeństwa.

Struktura Parametrów: Zamiast luźnego słownika, dostajesz listę obiektów. Łatwiej to potem iterować w kodzie Pythona:

Python

if result.tool_name == ToolName.SQL_DB:
    required_params = [p for p in result.parameters if p.is_required]
    # Sprawdzasz, czy masz wszystko, by odpalić SQL
Wskazówka dla Qwen 3 (8B)
Modele open-source, nawet z Pydantic, czasami lubią dodać tekst przed JSONem (np. "Sure, here is the JSON:"). PydanticOutputParser w LangChain zazwyczaj radzi sobie z wycięciem JSONa z tekstu, ale jeśli będziesz miała błędy parsowania, warto dodać w prompcie na końcu zdanie: OUTPUT ONLY THE JSON OBJECT. NO PREAMBLE.

