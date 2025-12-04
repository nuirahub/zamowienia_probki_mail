Oto kompletny przepis SQL na stworzenie "mostu" między Twoimi danymi twardymi (Klienci) a miękkimi (Notatki) w PostgreSQL przy użyciu pgvector.Koncepcja ArchitekturyZanim przejdziemy do kodu, spójrz na ten schemat. Kluczem jest to, że tabela wektorowa nie wisi w próżni. Jest ściśle powiązana z tabelą klientów kluczem obcym (client_id).Fragment koduerDiagram
    CLIENTS ||--o{ ORDERS : places
    CLIENTS ||--o{ MEETING_NOTES : has
    CLIENTS {
        int id PK
        string name
        string nip
        string owner
    }
    MEETING_NOTES {
        uuid id PK
        int client_id FK
        text content
        jsonb metadata
        vector embedding
    }
    ORDERS {
        int id PK
        int client_id FK
        date order_date
        decimal total_amount
    }
1. Kod SQL: Tworzenie tabeli pod RAGSkopiuj ten kod do swojego klienta SQL (np. pgAdmin lub DBeaver).SQL-- 1. Aktywuj rozszerzenie pgvector (jeśli jeszcze nie jest aktywne)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Załóżmy, że masz już tabelę klientów (uproszczony przykład)
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,    -- np. 'Budowlana', 'IT'
    owner_name TEXT   -- Opiekun klienta
);

-- 3. TWORZENIE TABELI NA NOTATKI (VECTOR STORE)
CREATE TABLE meeting_notes_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- KLUCZOWE: Powiązanie z tabelą SQL. 
    -- To pozwala na szybkie filtrowanie: "Daj notatki tylko klienta ID=5"
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Treść notatki (tzw. chunk)
    content TEXT NOT NULL,
    
    -- Metadane w formacie JSONB (bardzo szybkie w Postgresie)
    -- Tu trzymamy daty, autora notatki, typ spotkania
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Wektor. Liczba 1536 to wymiar dla OpenAI (text-embedding-3-small).
    -- Jeśli używasz lokalnych modeli (np. all-MiniLM-L6-v2), zmień na 384 lub 768.
    embedding vector(1536)
);

-- 4. INDEKSOWANIE (Dla wydajności przy dużej skali)

-- Indeks HNSW do szybkiego wyszukiwania podobieństwa (wektorów)
CREATE INDEX ON meeting_notes_embeddings USING hnsw (embedding vector_cosine_ops);

-- Indeks na client_id (do szybkiego łączenia z SQL)
CREATE INDEX ON meeting_notes_embeddings (client_id);

-- Indeks na metadane (pozwala szybko filtrować po dacie wewnątrz JSONa)
CREATE INDEX ON meeting_notes_embeddings USING GIN (metadata);
2. Jak wyglądają dane w środku?Gdy Twój skrypt Pythonowy (RAG) będzie przetwarzał notatkę, powinien wstawić do bazy taki rekord:KolumnaPrzykładowa Wartośćclient_id104 (To ID firmy "BudPol" z tabeli clients)content"Klient zgłaszał problem z terminowością dostaw w grudniu. Rozważa zmianę dostawcy, jeśli nie poprawimy logistyki."metadata{"date": "2023-12-15", "author": "Jan Kowalski", "type": "complaint"}embedding[0.012, -0.931, ...] (Tablica liczb)3. Jak o to pytać? (Magia Hybrid Search)To jest odpowiedź na Twoje pytanie: "Jak dobrać informacje by zbudować dane...?".Kiedy user pyta: "Jakie problemy zgłaszał BudPol w zeszłym roku?", Twój system (Python/LangChain) wykonuje następujące kroki:Krok SQL (Lookup): Najpierw znajduje ID dla "BudPol".SELECT id FROM clients WHERE name ILIKE '%BudPol%' -> Wynik: 104Krok Hybrid Search: Wykonuje zapytanie wektorowe, ale ograniczone do tego ID i daty.Oto jak wygląda zapytanie "hybrydowe" w SQL, które wysyła Twój RAG:SQLSELECT content, metadata
FROM meeting_notes_embeddings
WHERE 
    -- FILTR TWARDY (Metadata Filter)
    client_id = 104 
    AND (metadata ->> 'date')::DATE >= '2023-01-01'
    AND (metadata ->> 'date')::DATE <= '2023-12-31'
ORDER BY 
    -- SZUKANIE SEMANTYCZNE (Vector Search)
    -- Znajdź fragmenty najbardziej podobne do wektora słowa "problem"
    embedding <=> '[TU_WSTAW_WEKTOR_PYTANIA_USERA]'
LIMIT 5;
Dlaczego to jest lepsze niż trzymanie wszystkiego w wektorze?Precyzja: Jeśli zapytasz o "problemy BudPolu" w zwykłej bazie wektorowej, możesz dostać notatkę o "problemach firmy XYZ", bo semantycznie słowo "problem" jest podobne. Filtrując po client_id, eliminujesz ten błąd w 100%.Wydajność: Postgres najpierw odetnie 99% bazy (inne firmy), a potem przeszuka wektorowo tylko te kilka notatek BudPolu. To działa błyskawicznie.Daty: Modele wektorowe są fatalne w rozumieniu czasu ("tydzień temu", "w 2022"). SQL (WHERE date > ...) radzi sobie z tym doskonale.Rekomendacja:W LangChain użyj PGVector jako vector store. Obsługuje on przekazywanie parametrów filter (słownik), które są automatycznie tłumaczone na klauzulę WHERE w SQL.