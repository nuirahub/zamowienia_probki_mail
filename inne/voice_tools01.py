from langchain_core.tools import tool
from typing import Optional

# 1. Definiujemy funkcję i dekorujemy ją jako @tool
@tool
def get_client_snapshot(client_name: str, info_type: str = "general") -> dict:
    """
    Pobiera kluczowe informacje o kliencie z bazy CRM.
    Używaj tego narzędzia, gdy użytkownik pyta ogólnie o firmę, klienta, 
    jego adres, NIP lub opiekuna.

    Args:
        client_name: Nazwa firmy lub klienta (np. "Embraer", "Orlen").
        info_type: Typ informacji (domyślnie 'general', opcjonalnie 'finance' lub 'contact').
    """
    
    # --- TUTAJ NORMALNIE BYŁBY KOD SQL / API DO CRM ---
    # Symulacja danych na potrzeby testu (MOCK):
    print(f"\n[SYSTEM] Wywołuję funkcję get_client_snapshot dla: {client_name}...")
    
    mock_database = {
        "embraer": {
            "name": "Embraer S.A.", 
            "status": "VIP", 
            "region": "Brazylia", 
            "last_order": "2024-10-15",
            "account_manager": "Jan Kowalski"
        },
        "petrobras": {
            "name": "Petróleo Brasileiro", 
            "status": "STANDARD", 
            "region": "Brazylia",
            "last_order": "2024-09-01",
            "account_manager": "Anna Nowak"
        }
    }
    
    client_key = client_name.lower()
    result = mock_database.get(client_key, {"error": "Klient nie znaleziony w bazie."})
    return result