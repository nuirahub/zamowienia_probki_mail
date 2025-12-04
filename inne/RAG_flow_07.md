Zamiana "Nazwa" -> "ID" dzieje się w kodzie narzędzia, a nie w głowie modelu.

Oto kompletna definicja narzędzi (Tools) i Routera z wykorzystaniem Pydantic, przygotowana pod Twój stos technologiczny (Qwen 8B + LangChain).

1. Definicja Schematów Narzędzi (Tool Definitions)
Musimy zdefiniować dwie klasy Pydantic, które powiedzą modelowi, jakich argumentów potrzebuje każde z narzędzi.

Python

from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional

# --- Definicja Narzędzia 1: Baza Danych SQL (Twarde dane) ---
class SQLDatabaseInput(BaseModel):
    """
    Input schema dla narzędzia analitycznego SQL.
    Używane do pytań o liczby, listy, fakty, dane kontaktowe, stany magazynowe.
    """
    question: str = Field(
        description="Pełne pytanie użytkownika, które zostanie zamienione na kod SQL. "
                    "Np. 'Jaka jest wartość zamówień BudPolu?', 'Podaj email do Jana Kowalskiego'."
    )

# --- Definicja Narzędzia 2: Baza Wiedzy / Notatki (Miękkie dane) ---
class NotesKnowledgeBaseInput(BaseModel):
    """
    Input schema dla przeszukiwania wektorowego (pgvector).
    Używane do pytań o kontekst, ustalenia, opinie, historię relacji.
    """
    search_query: str = Field(
        description="Temat semantyczny, którego szukamy w notatkach. "
                    "Np. 'problemy z dostawą', 'plany na przyszły rok', 'opinie o kawie'."
    )
    client_name: Optional[str] = Field(
        default=None,
        description="Dokładna nazwa klienta, jeśli pytanie dotyczy konkretnej firmy. "
                    "Służy do filtrowania wyników (pre-filtering). Jeśli pytanie jest ogólne, zostaw puste."
    )
    time_frame: Optional[str] = Field(
        default=None,
        description="Określenie czasu, jeśli występuje w pytaniu. Np. 'last month', '2023'. "
                    "Pomoże w filtrowaniu metadanych."
    )
2. Definicja Routera (Struktura Wyjściowa)
Teraz definiujemy to, co Router ma nam zwrócić. Router ma wybrać, której z powyższych struktur (lub żadnej) użyć.

Python

from enum import Enum
from typing import Union

class ToolType(str, Enum):
    SQL_DB = "sql_db"
    VECTOR_SEARCH = "vector_search"
    NO_TOOL = "no_tool"

class RouterOutput(BaseModel):
    thinking: str = Field(
        description="Krótka analiza (Chain of Thought). Wyjaśnij, dlaczego wybierasz to narzędzie. "
                    "Czy pytanie dotyczy twardych danych (tabela) czy opisu słownego (tekst)?"
    )
    tool_name: ToolType = Field(description="Wybrane narzędzie.")
    
    # Argumenty dla narzędzi. Model wypełni tylko jedno z nich, reszta będzie null.
    sql_input: Optional[SQLDatabaseInput] = Field(description="Wypełnij to TYLKO jeśli wybierasz sql_db.")
    vector_input: Optional[NotesKnowledgeBaseInput] = Field(description="Wypełnij to TYLKO jeśli wybierasz vector_search.")
3. Prompt dla Routera (Instrukcja dla Qwen)
To jest instrukcja, która nauczy model Qwen mapować Twoje 4 obszary (produkty, klient, zamówienie, notatki) na te 2 narzędzia.

Python

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=RouterOutput)

router_template = """
You are an intelligent Router Agent for a Sales RAG system.
Your job is to route user questions to the correct data source based on the type of information needed.

AVAILABLE DATA SOURCES:

1. TOOL: "sql_db" (Structured Data)
   - Scope: Clients (Contact info, NIP, Address), Products (Price, Stock, Specs), Orders (Dates, Amounts, Items).
   - Use for: Exact lookups, aggregations, counting, contact details, lists of products bought.
   - Examples: 
     * "Jaki jest telefon do firmy X?" -> sql_db
     * "Ile kawy sprzedaliśmy w maju?" -> sql_db
     * "Kto jest opiekunem klienta Y?" -> sql_db

2. TOOL: "vector_search" (Unstructured Data / Notes)
   - Scope: Meeting notes, Emails, Call summaries.
   - Use for: Sentiment analysis, summarizing conversations, specific topics discussed, problems reported, future plans.
   - Examples:
     * "O czym rozmawialiśmy ostatnio z X?" -> vector_search
     * "Czy klienci narzekają na cenę kawy?" -> vector_search (Topic: "cena kawy", Client: None)
     * "Jakie ustalenia zapadły na spotkaniu z firmą Z?" -> vector_search

INSTRUCTIONS:
- Analyze the user question carefully.
- If the user asks for a contact person (name, email, phone), use 'sql_db' (this is in the Client table).
- If the user asks "When did I last see..." (meeting date), check if this implies checking a calendar/log (sql_db) or meeting notes (vector_search). Usually, specific dates of interactions are in SQL logs.
- Fill the 'thinking' field first.
- Output strictly in JSON format matching the schema.

{format_instructions}

USER QUESTION: {question}
"""

prompt = PromptTemplate(
    template=router_template,
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
4. Co się dzieje w kodzie ("Pod maską")?
To jest najważniejszy moment. Model zwrócił Ci JSONa, np.: tool_name="vector_search", client_name="BudPol".

Co z tym robisz w Pythonie? Musisz obsłużyć logikę "Nazwa -> ID".

Oto pseudokod logiki wykonawczej (Node w grafie LangChain):

Python

def run_vector_tool(input_data: NotesKnowledgeBaseInput):
    """
    To funkcja, która wykonuje się, gdy Router wybierze vector_search.
    """
    filter_dict = {}
    
    # 1. Rozwiązywanie nazwy klienta na ID (Magia!)
    if input_data.client_name:
        # Wykonujemy szybkie zapytanie SQL, żeby znaleźć ID
        # SELECT id FROM clients WHERE name ILIKE '%BudPol%' LIMIT 1
        client_id = db.run_sql(f"SELECT id FROM clients WHERE name ILIKE '%{input_data.client_name}%'")
        
        if client_id:
            filter_dict["client_id"] = client_id
    
    # 2. Obsługa daty (opcjonalnie)
    if input_data.time_frame:
        # Tu prosty parser daty zamienia "last month" na zakres dat
        start_date, end_date = parse_date(input_data.time_frame)
        filter_dict["date"] = {"$gte": start_date, "$lte": end_date}

    # 3. Właściwe wyszukiwanie w PGVector
    # LangChain automatycznie przetłumaczy filter_dict na SQL WHERE
    docs = vector_store.similarity_search(
        input_data.search_query,
        k=5,
        filter=filter_dict 
    )
    
    return docs
Dlaczego to rozwiązuje Twój problem?
Pytanie: "Podaj osoby kontaktowe dla klientów, którzy w ostatnim miesiącu zamówili produkty: kawa instant?"

Router widzi: "osoby kontaktowe", "zamówili", "produkty".

Decyzja: sql_db.

Parametry: question="Podaj osoby...".

Agent SQL dostaje całe zdanie i sam generuje JOINy (Klienci + Zamówienia + Produkty). Nie rozbijamy tego na Routerze.

Pytanie: "Z jakim klientem widziałem się w zeszłym tygodniu?"

Router widzi: "widziałem się" (spotkanie), "tydzień temu".

Decyzja: Tu możesz w prompcie wymusić, że historia kontaktów jest w sql_db (jeśli masz tabelę meetings lub logi w CRM). Router wybierze sql_db.

Pytanie: "O czym rozmawiałem z BudPolem przy kawie?"

Router widzi: "o czym" (kontekst), "BudPol".

Decyzja: vector_search.

Parametry: search_query="rozmowa przy kawie", client_name="BudPol".

Kod Pythona zamienia "BudPol" na ID i przeszukuje notatki tego konkretnego klienta.