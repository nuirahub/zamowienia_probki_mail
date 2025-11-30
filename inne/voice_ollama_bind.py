from langchain_ollama import ChatOllama

# 2. Konfiguracja modelu
# Ustawiamy temperature=0, aby model był precyzyjny przy wyborze narzędzi (mniej kreatywny).
llm = ChatOllama(
    model="qwen2.5:7b",  # Upewnij się, że masz ten model w 'ollama list'
    temperature=0
)

# 3. Wstrzyknięcie narzędzi do modelu
llm_with_tools = llm.bind_tools([get_client_snapshot])