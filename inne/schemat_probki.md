flowchart TD
    %% Definicje stylów z wymuszonym czarnym kolorem czcionki
    classDef db fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000000;
    classDef action fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000000;
    classDef email fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000000;
    classDef terminal fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000;

    subgraph MODULE_1 [Moduł 1: Weryfikacja Notatek]
        direction TB
        Start1((Start: Nowa Notatka)):::terminal --> GetNote[Pobierz treść notatki]
        GetNote --> CheckWord{{"Czy zawiera słowo\n'próbka'?"}}
        CheckWord -- TAK --> Stop1((Koniec)):::terminal
        CheckWord -- NIE --> CreateTask[Utwórz zadanie w TASKS]
        CreateTask --> DB_TASKS[("Baza Danych: TASKS")]
    end

    subgraph MODULE_2 [Moduł 2: Raportowanie i E-maile]
        direction TB
        Start2((Start: Harmonogram)):::terminal --> ReadDB[Pobierz dane z TASKS]
        DB_TASKS -.-> ReadDB
        ReadDB --> HasData{{"Czy są dane?"}}
        HasData -- NIE --> Stop2((Koniec)):::terminal
        HasData -- TAK --> GroupBy[Grupuj wg Sprzedawcy]
        
        GroupBy --> LoopStart{Dla każdego\nSprzedawcy}
        
        LoopStart --> Filter[Kategoryzacja Zadań]
        Filter --> Cat1[1. Nowe wpisy]
        Filter --> Cat2[2. Na dziś]
        Filter --> Cat3[3. Zaległe]
        
        Cat1 & Cat2 & Cat3 --> Compose[Zbuduj treść E-maila]
        Compose --> SendMail[/"Wyślij E-mail"/]
        
        SendMail --> LoopEnd{Kolejny\nSprzedawca?}
        LoopEnd -- TAK --> LoopStart
        LoopEnd -- NIE --> Stop3((Koniec Procesu)):::terminal
    end

    %% Przypisanie klas do elementów
    class DB_TASKS db;
    class CheckWord,HasData,LoopStart,LoopEnd decision;
    class GetNote,CreateTask,ReadDB,GroupBy,Filter,Cat1,Cat2,Cat3,Compose action;
    class SendMail email;

![Szablony symboli flowchart](../img/szablony-image.jpeg)



Elipsa / Koło (Start/Koniec): Oznacza wyzwalacz (Trigger) – np. "Codziennie o 8:00" lub "Nowa notatka".Romb (Decyzja/Bramka): Tu dzieje się logika "TAK/NIE". (np. "Czy zawiera słowo 'próbka'?").Prostokąt (Proces/Akcja): Konkretne działanie (np. "Pobierz notatki", "Wyślij e-mail").Cylinder (Baza Danych): Reprezentuje tabelę TASKS lub bazę notatek.Dokument / Ikona koperty: Symbolizuje wynik końcowy (E-mail do sprzedawcy).2. Logika przepływu (Jak to połączyć)Podziel diagram na dwa "tory" (swimlanes) lub dwa oddzielne pod-procesy.Moduł 1: Analiza Notatek (Generator Zadań)Tutaj kluczowy jest warunek negatywny (jeśli nie ma słowa "próbka").Start: Wyzwalacz (np. "Cykliczne sprawdzanie" lub "Zapisanie notatki").Akcja: Pobierz treść notatki.Decyzja (Romb): Czy tekst zawiera słowo "próbka"?TAK: Koniec (nie rób nic).NIE: Przejdź dalej.Akcja: Utwórz nowy rekord w tabeli TASKS (z przypisaniem do sprzedawcy i datą).Baza Danych: Zapis do TASKS.Moduł 2: Raportowanie (Dystrybutor)Tutaj kluczowa jest pętla (iteracja) po sprzedawcach i kategoryzacja danych.Start: Wyzwalacz (np. "Harmonogram: Codziennie rano").Baza Danych: Pobierz wszystkie rekordy z tabeli TASKS.Decyzja: Czy są dane? (Jeśli puste $\rightarrow$ Koniec).Akcja (Grupowanie): Pogrupuj zadania według Sprzedawcy.Pętla (Dla każdego sprzedawcy):Pod-proces (Filtr): Podziel zadania na 3 listy:List A: Nowe (utworzone np. w ciągu ostatnich 24h).List B: Na dziś (Deadline == Today).List C: Zaległe (Deadline < Today).Akcja: Wygeneruj treść e-maila (HTML/Text) z tymi trzema sekcjami.Wyjście: Wyślij E-mail.3. Wizualizacja (Gotowy kod do diagramu)Możesz użyć narzędzia takiego jak Mermaid.js, Lucidchart lub Draw.io. Poniżej przygotowałem gotowy kod w formacie Mermaid, który automatycznie wygeneruje Twój schemat.Fragment koduflowchart TD
    %% Definicje stylów
    classDef db fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef action fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef email fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;

    subgraph MODULE_1 [Moduł 1: Weryfikacja Notatek]
        Start1((Start: Nowa Notatka)) --> GetNote[Pobierz treść notatki]
        GetNote --> CheckWord{{"Czy zawiera słowo\n'próbka'?"}}
        CheckWord -- TAK --> Stop1((Koniec))
        CheckWord -- NIE --> CreateTask[Utwórz zadanie w TASKS]
        CreateTask --> DB_TASKS[("Baza Danych: TASKS")]
    end

    subgraph MODULE_2 [Moduł 2: Raportowanie i E-maile]
        Start2((Start: Harmonogram)) --> ReadDB[Pobierz dane z TASKS]
        DB_TASKS -.-> ReadDB
        ReadDB --> HasData{{"Czy są dane?"}}
        HasData -- NIE --> Stop2((Koniec))
        HasData -- TAK --> GroupBy[Grupuj wg Sprzedawcy]
        
        GroupBy --> LoopStart{Dla każdego\nSprzedawcy}
        
        LoopStart --> Filter[Kategoryzacja Zadań]
        Filter --> Cat1[1. Nowe wpisy]
        Filter --> Cat2[2. Na dziś]
        Filter --> Cat3[3. Zaległe]
        
        Cat1 & Cat2 & Cat3 --> Compose[Zbuduj treść E-maila]
        Compose --> SendMail[/"Wyślij E-mail"/]
        
        SendMail --> LoopEnd{Kolejny\nSprzedawca?}
        LoopEnd -- TAK --> LoopStart
        LoopEnd -- NIE --> Stop3((Koniec Procesu))
    end

    %% Przypisanie klas
    class DB_TASKS db;
    class CheckWord,HasData,LoopStart,LoopEnd decision;
    class GetNote,CreateTask,ReadDB,GroupBy,Filter,Cat1,Cat2,Cat3,Compose action;
    class SendMail email;
4. Jak opisać przepływy danych (Data Flow)?Na strzałkach (konektorach) warto dodać adnotacje, jakie dane są przekazywane:Moduł 1:Notatka $\rightarrow$ Decyzja: String (Treść notatki)Decyzja $\rightarrow$ DB: Object {Tytuł, ID_Sprzedawcy, Data_Utworzenia, Status='Open'}Moduł 2:DB $\rightarrow$ Procesor: Array of Objects (Lista Zadań)Procesor $\rightarrow$ E-mail: HTML String (Sformatowana tabela)Podsumowanie - co zawierać na diagramie:Punkty decyzyjne: Jasno zaznacz warunki ("próbka", "pusta tabela").Interakcje z bazą: Pokaż moment zapisu (Moduł 1) i moment odczytu (Moduł 2).Stan "Zaległe/Na Dziś": To logika biznesowa, warto ją wyszczególnić jako proces "Sortowania/Filtrowania", a nie czarną skrzynkę.Pętlę (Loop): Ważne, aby pokazać, że system wysyła wiele maili (jeden per sprzedawca), a nie jeden zbiorczy.Czy chciałbyś, abym rozpisał szczegółowo strukturę bazy danych (jakie kolumny powinna mieć tabela TASKS), aby obsłużyć te trzy kategorie (nowe/dziś/zaległe)?