1. Konfiguracja Połączenia
Najpierw musimy ustawić połączenie, z którego skorzystają oba narzędzia.

Python

import psycopg2
from langchain_community.utilities import SQLDatabase
from langchain_postgres import PGVector
from langchain_community.embeddings import OllamaEmbeddings # Lub OpenAIEmbeddings

# Konfiguracja połączenia do bazy
DB_URI = "postgresql+psycopg2://user:password@localhost:5432/twoja_baza"

# 1. Obiekt do SQL Tool (LangChain wrapper na SQLAlchemy)
db = SQLDatabase.from_uri(DB_URI)

# 2. Obiekt do Vector Store
# Ważne: collection_name to nazwa tabeli, którą stworzyłaś w SQL (meeting_notes_embeddings)
embeddings = OllamaEmbeddings(model="nomic-embed-text") # Przykład dla lokalnego modelu
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="meeting_notes_embeddings",
    connection=DB_URI,
    use_jsonb=True,
)
2. Implementacja run_vector_search (Notatki + ID Lookup)
Tutaj realizujemy strategię: Najpierw znajdź ID klienta, potem filtruj notatki.

Python

def get_client_id_by_name(name: str) -> int | None:
    """
    Pomocnicza funkcja, która zamienia "BudPol" na 104.
    Używamy czystego SQL dla szybkości.
    """
    # Uważaj na SQL Injection w produkcji! Tutaj uproszczony przykład.
    clean_name = name.replace("'", "") 
    query = f"SELECT id FROM clients WHERE name ILIKE '%{clean_name}%' LIMIT 1;"
    
    try:
        # Używamy db z LangChain do wykonania surowego zapytania
        result_str = db.run(query) 
        # db.run zwraca string, np. "[(104,)]" lub pusty, trzeba to sparsować
        import ast
        result = ast.literal_eval(result_str)
        if result and len(result) > 0:
            return result[0][0] # Zwraca ID, np. 104
    except Exception as e:
        print(f"Błąd przy szukaniu klienta: {e}")
    return None

def run_vector_tool(search_query: str, client_name: str = None, time_frame: str = None):
    """
    Główna funkcja wykonawcza dla narzędzia vector_search.
    """
    filter_args = {}

    # KROK 1: Rozwiązywanie nazwy klienta na ID
    if client_name:
        client_id = get_client_id_by_name(client_name)
        if client_id:
            # Składnia filtra dla PGVector (zależy od wersji, zazwyczaj dict mapuje na metadane lub kolumny)
            # W langchain-postgres filter działa na metadanych JSONB lub kolumnach zewnętrznych
            # Tutaj zakładamy filtr na kolumnę relacyjną 'client_id' jeśli vector store to wspiera,
            # lub częściej: filtrujemy po metadanych (musisz dodawać client_id do metadanych przy zapisie!)
            
            filter_args["client_id"] = client_id 
            print(f"🔎 DEBUG: Znaleziono ID klienta: {client_id}. Filtruję wyniki.")
        else:
            print(f"⚠️ DEBUG: Nie znaleziono klienta o nazwie '{client_name}'. Szukam w całej bazie.")

    # KROK 2: Wyszukiwanie (Similarity Search)
    # k=5 oznacza pobranie 5 najbardziej pasujących fragmentów
    docs = vector_store.similarity_search(
        search_query,
        k=5,
        filter=filter_args if filter_args else None
    )

    # KROK 3: Formatowanie wyników dla LLM
    # Nie zwracamy surowych obiektów Document, tylko czysty tekst
    if not docs:
        return "Nie znaleziono żadnych notatek pasujących do zapytania."

    formatted_results = "\n\n".join([
        f"--- Notatka (Data: {doc.metadata.get('date', 'Brak daty')}) ---\n{doc.page_content}" 
        for doc in docs
    ])
    
    return formatted_results
Ważna uwaga o filtrach w PGVector: Aby filter={"client_id": 104} zadziałał, przy dodawaniu dokumentów do bazy (indeksowaniu), musisz upewnić się, że client_id znajduje się w metadanych dokumentu, np.: doc = Document(page_content="...", metadata={"client_id": 104, "date": "..."})

3. Implementacja run_sql_tool (Text-to-SQL)
W przypadku Qwen-8B nie możemy polegać na tym, że model sam idealnie wymyśli zapytanie. Użyjemy łańcucha create_sql_query_chain, który automatycznie wstrzykuje schemat tabel do promptu.

Python

from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama

# Model do SQL (może mieć wyższe temperature niż Router, np. 0.1)
llm_sql = Ollama(model="qwen2.5:7b", temperature=0.1)

# Narzędzie wykonawcze (to ono faktycznie puszcza query do bazy)
execute_query = QuerySQLDataBaseTool(db=db)

# Łańcuch generowania SQL
write_query = create_sql_query_chain(llm_sql, db)

def run_sql_tool(user_question: str):
    """
    Funkcja generująca i wykonująca SQL na podstawie pytania naturalnego.
    """
    try:
        # KROK 1: Generowanie SQL
        # create_sql_query_chain sam pobiera schemat tabeli i wstawia go do promptu
        generated_sql = write_query.invoke({"question": user_question})
        
        # Oczyszczanie SQL (Qwen czasem dodaje "Here is the SQL: ```sql ... ```")
        cleaned_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        # Czasami model zwraca "SQLQuery: SELECT...", trzeba to uciąć
        if "SQLQuery:" in cleaned_sql:
            cleaned_sql = cleaned_sql.split("SQLQuery:")[1].strip()

        print(f"📝 DEBUG: Wygenerowany SQL: {cleaned_sql}")

        # KROK 2: Wykonanie SQL
        result = execute_query.invoke(cleaned_sql)
        
        return f"Wynik z bazy danych:\n{result}"

    except Exception as e:
        return f"Błąd podczas pobierania danych z bazy SQL: {str(e)}"
4. Główna pętla sterująca (Orchestrator)
Teraz spinamy wszystko razem. To jest kod, który uruchamiasz w swojej aplikacji (np. Streamlit lub API).

Python

# Zakładam, że masz już zdefiniowany `chain` routera z poprzedniej odpowiedzi

def process_user_query(user_input: str):
    # 1. Uruchom Router
    router_response = chain.invoke({"question": user_input})
    
    print(f"🤖 ROUTER: Wybrano narzędzie: {router_response.tool_name}")
    print(f"🧠 MYŚLENIE: {router_response.thinking}")

    final_context = ""

    # 2. Wykonaj odpowiednie narzędzie
    if router_response.tool_name == "sql_db":
        # Jeśli router wybrał SQL, bierzemy parametry z sql_input
        # Ale w praktyce SQL tool potrzebuje po prostu oryginalnego pytania, 
        # bo sam sobie z niego wyciągnie co trzeba.
        params = router_response.sql_input
        if params:
            final_context = run_sql_tool(params.question)
        else:
            # Fallback jeśli model nie wypełnił inputu
            final_context = run_sql_tool(user_input)

    elif router_response.tool_name == "vector_search":
        params = router_response.vector_input
        if params:
            final_context = run_vector_tool(
                search_query=params.search_query,
                client_name=params.client_name,
                time_frame=params.time_frame
            )
        else:
            final_context = "Błąd: Router wybrał vector_search, ale nie podał parametrów."

    elif router_response.tool_name == "no_tool":
        return "Nie znalazłem w bazie wiedzy informacji na ten temat. Czy możesz doprecyzować?"

    # 3. Synteza ostatecznej odpowiedzi (Final Generation)
    # Teraz bierzemy "brudne" dane (context) i prosimy LLM o ładną odpowiedź dla człowieka.
    
    final_prompt = f"""
    Jesteś asystentem sprzedaży. Odpowiedz na pytanie użytkownika, korzystając z poniższych informacji pobranych z systemu.
    
    PYTANIE UŻYTKOWNIKA: {user_input}
    
    INFORMACJE Z SYSTEMU (Kontekst):
    {final_context}
    
    Jeżeli informacje z systemu zawierają błąd lub są puste, powiedz o tym uczciwie.
    Odpowiedz zwięźle i profesjonalnie po polsku.
    """
    
    # Używamy tego samego modelu co do routera lub innego
    final_answer = llm.invoke(final_prompt)
    return final_answer
Podsumowanie techniczne:
Dla SQL: Cała trudność leży w dobrym wygenerowaniu zapytania. create_sql_query_chain robi większość roboty, ale dla modelu 8B upewnij się, że nazwy kolumn w bazie są po angielsku i są "samo-wyjaśniające" (np. total_price zamiast col_a), albo użyj parametru db.get_table_info() w prompcie, aby model widział opisy.

Dla Vector: Kluczem jest funkcja get_client_id_by_name. Bez niej system wektorowy będzie "ślepy" na to, czyj to jest kontekst.