# Przełączanie między CSV a SQL

## Konfiguracja

Aby przełączyć się między danymi z CSV (prototyp/testy) a SQL (produkcja), wystarczy zmienić jedną zmienną w pliku `.env`:

### Tryb CSV (prototyp/testy)
```ini
USE_MOCK_DATA=True
```

### Tryb SQL (produkcja)
```ini
USE_MOCK_DATA=False
DB_SERVER=adres_serwera
DB_NAME=nazwa_bazy
DB_USER=uzytkownik
DB_PASSWORD=haslo
```

## Struktura plików CSV

Pliki CSV powinny znajdować się w katalogu `data/mocks/`:

- `customers.csv` - dane klientów
- `notes.csv` - notatki
- `samples.csv` - próbki

### Format plików CSV

Pliki używają separatora `;` (średnik) i kodowania UTF-8 z BOM (utf-8-sig).

#### customers.csv
```csv
id;name;email;phone;created_at
CUST_001;Jan Kowalski;j.kowalski@example.com;+48123456789;2023-01-15
```

#### notes.csv
```csv
id;customer_id;content;created_at;is_processed
1;CUST_001;Treść notatki;2023-11-20;False
```

#### samples.csv
```csv
id;customer_id;status;date_sent;notes
1;CUST_001;Sent;2023-11-20;Dodatkowe informacje
```

### Format dat

Daty mogą być w formacie:
- `YYYY-MM-DD` (np. `2023-11-20`)
- `DD.MM.YYYY` (np. `20.11.2023`)
- `YYYY-MM-DD HH:MM:SS` (np. `2023-11-20 14:30:00`)

## Użycie w kodzie

### Przed (bezpośrednie użycie repozytoriów SQL)
```python
from company_lib.core.database import MSSQLConnection
from company_lib.domain.repositories import NoteRepository

with MSSQLConnection(Config.DB_STRING) as db:
    note_repo = NoteRepository(db)
    notes = note_repo.get_all_notes()
```

### Po (użycie fabryki - automatyczne przełączanie)
```python
from company_lib.infrastructure.factories import get_note_repository

note_repo = get_note_repository()  # Automatycznie wybiera CSV lub SQL
notes = note_repo.get_all_notes()
```

## Testy jednostkowe

Repozytoria CSV są idealne do testów jednostkowych, ponieważ:
- Nie wymagają połączenia z bazą danych
- Działają szybko (dane w pamięci)
- Są bezpieczne (nie modyfikują danych produkcyjnych)
- Są powtarzalne (zawsze te same dane)

### Przykład testu
```python
import pytest
from company_lib.infrastructure.repo_csv import CsvNoteRepository
from pathlib import Path

def test_get_pending_notes():
    repo = CsvNoteRepository(Path("data/mocks/notes.csv"))
    notes = repo.get_all_notes(processed=False)
    assert len(notes) > 0
    assert all(not note.is_processed for note in notes)
```

## Zalety tego podejścia

1. **Łatwe przełączanie**: Jedna zmienna w `.env`
2. **Bezpieczne testy**: Testy nie wymagają bazy danych
3. **Szybki prototyp**: Możesz pracować bez dostępu do SQL
4. **Czysty kod**: Logika biznesowa nie wie, skąd pochodzą dane
5. **Zgodność interfejsów**: CSV i SQL implementują te same interfejsy

