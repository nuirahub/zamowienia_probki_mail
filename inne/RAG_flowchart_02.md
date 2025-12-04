graph TD
    %% Definicje stylów
    classDef user fill:#f9f,stroke:#333,stroke-width:2px,color:black;
    classDef router fill:#bbf,stroke:#333,stroke-width:2px,color:black;
    classDef process fill:#fff,stroke:#333,stroke-width:1px,color:black;
    classDef db fill:#dfd,stroke:#333,stroke-width:2px,color:black;
    classDef llm fill:#ffd,stroke:#333,stroke-width:2px,color:black;

    %% Węzły
    Start([👤 Sprzedawca wpisuje pytanie]):::user
    Router{🤖 Router / Agent<br/>(Klasyfikacja Intencji)}:::router
    
    %% Ścieżka 1: Dane twarde (SQL)
    subgraph SQL_Path [Ścieżka Danych Ustrukturyzowanych]
        GenSQL[Generowanie zapytania SQL<br/>Text-to-SQL]:::process
        ExecSQL[Wykonywanie SQL]:::process
        DataResult[📅 Wynik: Tabela/Liczba<br/>(np. Suma zamówień, Adres)]:::process
    end

    %% Ścieżka 2: Dane miękkie (Vector)
    subgraph Vector_Path [Ścieżka Danych Nieustrukturyzowanych]
        Embed[Zamiana pytania na Wektory<br/>Embeddings]:::process
        Search[Wyszukiwanie Semantyczne<br/>Top-k chunks]:::process
        TextResult[📝 Wynik: Fragmenty Notatek<br/>(np. Opis problemu, Sentyment)]:::process
    end

    %% Bazy Danych
    DB_Struct[(🗄️ Baza SQL/CSV<br/>Klienci, Produkty, Zamówienia)]:::db
    DB_Vector[(🗄️ Baza Wektorowa<br/>Notatki ze spotkań)]:::db

    %% Połączenia logiczne
    Start --> Router

    %% Decyzje Routera
    Router -- "Pytanie o fakty/liczby" --> GenSQL
    Router -- "Pytanie o kontekst/opinię" --> Embed
    Router -- "Pytanie Hybrydowe" --> GenSQL & Embed

    %% Przepływ danych
    GenSQL --> ExecSQL
    ExecSQL <--> DB_Struct
    ExecSQL --> DataResult

    Embed --> Search
    Search <--> DB_Vector
    Search --> TextResult

    %% Synteza
    DataResult --> Context{📑 Budowanie Kontekstu}
    TextResult --> Context
    
    Context --> FinalLLM[🧠 LLM Generujący Odpowiedź<br/>Synteza i formatowanie]:::llm
    FinalLLM --> End([💬 Gotowa odpowiedź dla Sprzedawcy]):::user



    --------------------------------
    Objaśnienie kluczowych elementów schematu:
Router (Klasyfikator Intencji):

To najważniejszy element w Twoim przypadku. Kiedy sprzedawca pyta: "Ile wydali klienci, którzy narzekali na jakość?", Router musi rozbić to na dwa zadania:

Zadanie A (Vector): Znajdź klientów, którzy "narzekali na jakość" w notatkach.

Zadanie B (SQL): Policz sumę zamówień dla znalezionych klientów.

Ścieżka SQL (Baza SQL/CSV):

Tu trafiają pliki: Lista klientów, Lista produktów, Zamówienia.

LLM zamienia pytanie (np. "Jaka jest cena produktu X?") na kod SQL (SELECT price FROM products WHERE name = 'X'). To gwarantuje 100% precyzji w liczbach (czego zwykły ChatGPT często nie potrafi zrobić "z pamięci").

Ścieżka Wektorowa (Baza Notatek):

Tu trafiają Twoje Notatki ze spotkań.

Notatki są dzielone na kawałki, zamieniane na liczby (wektory) i przeszukiwane pod kątem znaczenia, a nie tylko słów kluczowych (dzięki temu system wie, że "zły nastrój" to to samo co "sfrustrowany").

Synteza (Final LLM):

Na końcu system dostaje "wsad" z obu źródeł (np. tabelkę z Excela + 3 fragmenty notatek) i na tej podstawie pisze naturalną odpowiedź dla człowieka, np.: "Klient X wydał w tym roku 50 000 PLN, ale w notatce z 12.05 zgłaszał problem z dostawą, dlatego warto poruszyć ten temat ostrożnie."