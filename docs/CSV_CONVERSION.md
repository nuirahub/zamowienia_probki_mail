# Proces Konwersji CSV ↔ Obiekty

## Moment konwersji

Konwersja z CSV na obiekty (`List[SampleModel]`) następuje w **dwóch krokach**:

### Krok 1: Odczyt CSV → Słownik (Dict)
```python
# W CsvGenericRepository.load_all()
reader = csv.DictReader(f, delimiter=';')
# row = {'id': '1', 'customer_id': 'CUST_001', 'status': 'Sent', 'date_sent': '2025-11-19', ...}
```

### Krok 2: Słownik → Obiekt (SampleModel)
```python
# W CsvGenericRepository._map_row_to_types()
typed_data = self._map_row_to_types(row)
# typed_data = {'id': 1, 'customer_id': 'CUST_001', 'status': 'Sent', 'date_sent': datetime(2025, 11, 19), ...}

# Tworzenie obiektu
results.append(self.model_cls(**typed_data))
# SampleModel(id=1, customer_id='CUST_001', status='Sent', date_sent=datetime(2025, 11, 19), ...)
```

## Format CSV dla SampleModel

Aby `List[SampleModel]` miała poprawnie zdefiniowane typy, CSV musi mieć:

### Wymagane kolumny:
- `id` - liczba całkowita
- `customer_id` - string
- `status` - string
- `date_sent` - data w formacie: `YYYY-MM-DD` (preferowany) lub `DD.MM.YYYY`

### Opcjonalne kolumny:
- `notes` - string (może być puste)

### Przykład poprawnego CSV:
```csv
id;customer_id;status;date_sent;notes
1;CUST_001;Sent;2025-11-19;Próbki kawy arabica
2;CUST_002;Sent;2025-11-14;Próbki kawy robusta
```

## Obsługiwane formaty dat

Metoda `_map_row_to_types()` próbuje następujące formaty (w kolejności):
1. `%Y-%m-%d` - `2025-11-19` ✅ **REKOMENDOWANY**
2. `%d.%m.%Y` - `19.11.2025`
3. `%Y-%m-%d %H:%M:%S` - `2025-11-19 14:30:00`
4. `%d.%m.%Y %H:%M:%S` - `19.11.2025 14:30:00`

## Problemy i rozwiązania

### Problem 1: Data nie jest parsowana
**Przyczyna:** Format daty nie jest obsługiwany

**Rozwiązanie:** Użyj formatu `YYYY-MM-DD`:
```csv
date_sent
2025-11-19  ✅
19.11.2025  ✅
2025/11/19  ❌ (nie obsługiwane)
```

### Problem 2: Pole int jest puste
**Przyczyna:** Puste pole dla wymaganego `int`

**Rozwiązanie:** Wypełnij wszystkie wymagane pola:
```csv
id;customer_id;status;date_sent
1;CUST_001;Sent;2025-11-19  ✅
;CUST_001;Sent;2025-11-19   ❌ (brak id)
```

### Problem 3: Optional[datetime] jest puste
**Przyczyna:** Puste pole dla opcjonalnej daty

**Rozwiązanie:** Zostaw puste lub użyj wartości domyślnej:
```csv
notes;created_at
Próbki kawy;2025-11-19  ✅
Próbki kawy;            ✅ (None jeśli Optional)
```

## Weryfikacja konwersji

Aby sprawdzić czy konwersja działa poprawnie:

```python
from company_lib.infrastructure.repo_csv import CsvSampleRepository
from pathlib import Path

repo = CsvSampleRepository(Path("data/mocks/samples.csv"))
samples = repo.load_all()

# Sprawdź typy
for sample in samples:
    print(f"ID: {sample.id} (type: {type(sample.id)})")
    print(f"Date: {sample.date_sent} (type: {type(sample.date_sent)})")
    # Powinno być: <class 'int'> i <class 'datetime.datetime'>
```

