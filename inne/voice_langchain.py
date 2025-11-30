# A. Pierwsze wywołanie modelu (Decyzja)
ai_msg = llm_with_tools.invoke(messages)

# Sprawdźmy, co wymyślił model
if ai_msg.tool_calls:
    print(f"[AI] Model chce użyć narzędzi: {ai_msg.tool_calls}")
    
    # B. Wykonanie narzędzia
    for tool_call in ai_msg.tool_calls:
        # LangChain automatycznie mapuje nazwę funkcji
        selected_tool = {"get_client_snapshot": get_client_snapshot}[tool_call["name"].lower()]
        
        # Uruchamiamy funkcję z argumentami wygenerowanymi przez AI
        tool_output = selected_tool.invoke(tool_call["args"])
        
        # C. Dodajemy wynik funkcji do historii rozmowy
        # Musimy to odesłać do modelu jako 'ToolMessage'
        from langchain_core.messages import ToolMessage
        
        messages.append(ai_msg) # Dodajemy decyzję modelu
        messages.append(ToolMessage(
            content=str(tool_output), # Surowy wynik (JSON/Dict)
            tool_call_id=tool_call["id"]
        ))
        
    # D. Drugie wywołanie modelu (Synteza odpowiedzi)
    # Model widzi teraz: Pytanie -> Swoją decyzję -> Wynik funkcji -> I generuje odpowiedź
    final_response = llm_with_tools.invoke(messages)
    
    print("\n[ODPOWIEDŹ BOTA]:")
    print(final_response.content)

else:
    # Jeśli model nie chciał użyć narzędzia (zwykła rozmowa)
    print(ai_msg.content)