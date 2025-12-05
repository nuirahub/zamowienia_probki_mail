import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql

# 1. Konfiguracja połączenia do bazy
DB_CONFIG = {
    "dbname": "twoja_baza",
    "user": "twoj_user",
    "password": "twoje_haslo",
    "host": "localhost",
    "port": "5432"
}

# --- UNIWERSALNA FUNKCJA INSERT ---
def generic_insert(cursor, table_name, data_list):
    """
    Wstawia listę słowników do podanej tabeli.
    Klucze słownika muszą pasować do nazw kolumn w bazie.
    
    :param cursor: Kursor bazy danych
    :param table_name: Nazwa tabeli (string)
    :param data_list: Lista słowników z danymi, np. [{'imie': 'Jan', 'wiek': 30}, ...]
    """
    if not data_list:
        return
    
    # Pobieramy klucze (nazwy kolumn) z pierwszego elementu
    columns = list(data_list[0].keys())
    
    # Budowanie dynamicznego zapytania SQL
    # Używamy sql.Identifier dla nazw tabeli/kolumn dla bezpieczeństwa
    # Używamy %s dla wartości (placeholder)
    
    query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
        table=sql.Identifier(table_name),
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        values=sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )
    
    # Przygotowanie danych do executemany (lista krotek)
    values_to_insert = [tuple(item[col] for col in columns) for item in data_list]
    
    try:
        # executemany wykonuje to samo zapytanie dla wielu rekordów
        cursor.executemany(query, values_to_insert)
        print(f"✅ Pomyślnie dodano {len(data_list)} rekordów do tabeli '{table_name}'.")
    except Exception as e:
        print(f"❌ Błąd przy insercie do '{table_name}': {e}")
        raise e

# --- FUNKCJA SCRAPUJĄCA ---
def scrape_data(url):
    print(f"🔄 Pobieranie danych z {url}...")
    response = requests.get(url)
    if response.status_code != 200:
        print("Błąd połączenia ze stroną")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    # PRZYKŁAD: Szukamy divów z klasą 'person-card' (to trzeba dostosować do Twojej strony!)
    cards = soup.find_all('div', class_='person-card')
    
    for card in cards:
        # Wyciągamy dane i tworzymy słownik
        # Klucze muszą nazywać się tak jak kolumny w Twoim Postgresie!
        person = {
            'imie_nazwisko': card.find('h2').get_text(strip=True),
            'stanowisko': card.find('span', class_='role').get_text(strip=True),
            'email': card.find('a', class_='email')['href'].replace('mailto:', '')
        }
        results.append(person)
        
    return results

# --- GŁÓWNY PROGRAM ---
def main():
    target_url = "https://przykladowa-strona-firmowa.pl/zespol"
    
    # 1. Ściągnij dane
    scraped_data = scrape_data(target_url)
    
    if not scraped_data:
        print("Brak danych do zapisania.")
        return

    # 2. Połącz z bazą i zapisz
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # UŻYCIE UNIWERSALNEJ FUNKCJI
        # Zauważ: Tabela musi istnieć, a klucze w scraped_data muszą pasować do kolumn
        generic_insert(cur, 'pracownicy', scraped_data)
        
        conn.commit() # Zatwierdzenie zmian
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Błąd bazy danych: {e}")

if __name__ == "__main__":
    main()