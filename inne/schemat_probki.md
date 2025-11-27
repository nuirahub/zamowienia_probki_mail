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