# Proces Konwersji CSV - Szczegółowy Przepływ

## Diagram przepływu

```
CSV FILE (tekst)
    ↓
csv.DictReader (linia 57)
    ↓
row = {'id': '1', 'date_sent': '2025-11-19', ...}  ← Wszystko jako STRING
    ↓
_map_row_to_types(row) (linia 62)
    ↓
typed_data = {'id': 1, 'date_sent': datetime(2025, 11, 19), ...}  ← Konwersja typów
    ↓
self.model_cls(**typed_data) (linia 63)
    ↓
SampleModel(id=1, date_sent=datetime(2025, 11, 19), ...)  ← OBIEKT
    ↓
List[SampleModel]  ← WYNIK
```

## Krok po kroku

### 1. Odczyt pliku CSV
```python
# Linia 56-57 w repo_csv.py
with open(self.file_path, mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
```

**Wynik:** Każdy wiersz to słownik z wartościami jako **stringi**:
```python
row = {
    'id': '1',                    # ← STRING
    'customer_id': 'CUST_001',    # ← STRING
    'status': 'Sent',              # ← STRING
    'date_sent': '2025-11-19',    # ← STRING (nie datetime!)
    'notes': 'Próbki kawy'        # ← STRING
}
```

### 2. Konwersja typów (_map_row_to_types)
```python
# Linia 78-145 w repo_csv.py
typed_data = self._map_row_to_types(row)
```

**Proces konwersji dla każdego pola:**

#### Pole `id` (int):
```python
target_type = int
value = '1'  # z CSV
data['id'] = int('1')  # → 1 (int)
```

#### Pole `date_sent` (datetime):
```python
target_type = datetime
value = '2025-11-19'  # z CSV
# Próbuje format '%Y-%m-%d'
data['date_sent'] = datetime.strptime('2025-11-19', '%Y-%m-%d')
# → datetime(2025, 11, 19, 0, 0)
```

#### Pole `notes` (Optional[str]):
```python
target_type = Optional[str]
value = 'Próbki kawy'  # z CSV
# Optional[str] → weź str
data['notes'] = 'Próbki kawy'  # → string
```

**Wynik:**
```python
typed_data = {
    'id': 1,                                    # ← INT
    'customer_id': 'CUST_001',                  # ← STRING
    'status': 'Sent',                          # ← STRING
    'date_sent': datetime(2025, 11, 19, 0, 0),  # ← DATETIME
    'notes': 'Próbki kawy'                     # ← STRING
}
```

### 3. Tworzenie obiektu
```python
# Linia 63 w repo_csv.py
results.append(self.model_cls(**typed_data))
# Równoważne z:
results.append(SampleModel(
    id=1,
    customer_id='CUST_001',
    status='Sent',
    date_sent=datetime(2025, 11, 19, 0, 0),
    notes='Próbki kawy'
))
```

**Wynik:** Obiekt `SampleModel` z poprawnymi typami

## Jak zapisać CSV aby typy były poprawne

### Metoda 1: Użyj metody `save_all()` (REKOMENDOWANA)

```python
from company_lib.infrastructure.repo_csv import CsvSampleRepository
from company_lib.domain.models import SampleModel
from datetime import datetime

# Utwórz obiekty
samples = [
    SampleModel(
        id=1,
        customer_id='CUST_001',
        status='Sent',
        date_sent=datetime(2025, 11, 19),
        notes='Próbki kawy'
    )
]

# Zapisz
repo = CsvSampleRepository(Path("data/mocks/samples.csv"))
repo.save_samples(samples)  # Automatyczna konwersja do CSV
```

**Wynikowy CSV:**
```csv
id;customer_id;status;date_sent;notes
1;CUST_001;Sent;2025-11-19;Próbki kawy
```

### Metoda 2: Ręczne formatowanie (jeśli edytujesz w Excelu)

**Format daty:** `YYYY-MM-DD`
```csv
date_sent
2025-11-19  ✅ Poprawne
19.11.2025  ✅ Poprawne (alternatywny format)
2025/11/19  ❌ Nie obsługiwane
```

**Format boolean:** `True`/`False` lub `1`/`0`
```csv
is_processed
True   ✅
False  ✅
1      ✅
0      ✅
tak    ✅
```

**Puste opcjonalne pola:** Zostaw puste
```csv
notes
Próbki kawy  ✅
            ✅ (None dla Optional[str])
```

## Weryfikacja po odczycie

```python
repo = CsvSampleRepository(Path("data/mocks/samples.csv"))
samples = repo.load_all()  # List[SampleModel]

# Sprawdź typy
for sample in samples:
    assert isinstance(sample.id, int)  # ✅
    assert isinstance(sample.date_sent, datetime)  # ✅
    assert isinstance(sample.customer_id, str)  # ✅
    
    # Możesz używać operacji na datach
    days_ago = (datetime.now() - sample.date_sent).days
    print(f"Próbka wysłana {days_ago} dni temu")
```

## Najczęstsze błędy

### Błąd 1: Data nie jest datetime
**Problem:**
```python
sample.date_sent > datetime.now()  # TypeError: '>' not supported between 'str' and 'datetime'
```

**Przyczyna:** CSV ma datę w nieobsługiwanym formacie

**Rozwiązanie:** Użyj formatu `YYYY-MM-DD` w CSV

### Błąd 2: ID jest stringiem
**Problem:**
```python
sample.id + 1  # TypeError: can only concatenate str (not "int") to str
```

**Przyczyna:** W CSV jest tekst zamiast liczby

**Rozwiązanie:** Upewnij się że w CSV jest `1` a nie `"1"` (ale csv.DictReader zawsze zwraca stringi, więc konwersja powinna działać)

### Błąd 3: Puste pole dla wymaganego typu
**Problem:**
```python
# Błąd przy tworzeniu obiektu - brakuje wymaganego pola
```

**Przyczyna:** W CSV brakuje wartości dla wymaganego pola

**Rozwiązanie:** Wypełnij wszystkie wymagane pola w CSV

