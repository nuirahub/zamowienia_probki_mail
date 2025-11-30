from langchain_core.messages import HumanMessage, SystemMessage

# Definicja System Promptu - to jest kluczowe dla jakości
system_prompt = """
Jesteś asystentem korporacyjnym wspierającym pracowników w terenie.
Masz dostęp do narzędzi umożliwiających pobieranie danych o klientach.

ZASADY:
1. ZAWSZE najpierw sprawdź, czy masz narzędzie pasujące do pytania użytkownika.
2. Jeśli użytkownik pyta o klienta, uruchom 'get_client_snapshot'.
3. Nie zgaduj danych. Jeśli funkcja zwróci błąd, powiedz o tym użytkownikowi.
4. Odpowiadaj krótko i rzeczowo w języku polskim.
"""

# Przykładowe zapytanie użytkownika
user_query = "Daj mi szybkie info o kliencie Embraer."

# Zbudowanie listy wiadomości
messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_query)
]