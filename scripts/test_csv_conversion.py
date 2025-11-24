"""
Skrypt testowy do weryfikacji konwersji CSV ↔ Obiekty.
Pokazuje jak działa konwersja i jak poprawnie zapisać CSV.
"""
import sys
import io
from pathlib import Path
from datetime import datetime
from company_lib.infrastructure.repo_csv import CsvSampleRepository
from company_lib.domain.models import SampleModel
from company_lib.config import Config

# Napraw kodowanie dla Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_csv_reading():
    """Test odczytu CSV i weryfikacji typów."""
    print("=" * 60)
    print("TEST 1: Odczyt CSV i weryfikacja typów")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    repo = CsvSampleRepository(Config.MOCK_DIR / "samples.csv")
    samples = repo.load_all()
    
    print(f"\nWczytano {len(samples)} próbek z CSV\n")
    
    for i, sample in enumerate(samples, 1):
        print(f"Próbka {i}:")
        print(f"  ID: {sample.id} (typ: {type(sample.id).__name__})")
        print(f"  Customer ID: {sample.customer_id} (typ: {type(sample.customer_id).__name__})")
        print(f"  Status: {sample.status} (typ: {type(sample.status).__name__})")
        print(f"  Date Sent: {sample.date_sent} (typ: {type(sample.date_sent).__name__})")
        print(f"  Notes: {sample.notes} (typ: {type(sample.notes).__name__})")
        
        # Weryfikacja typów
        assert isinstance(sample.id, int), f"ID powinno być int, jest {type(sample.id)}"
        assert isinstance(sample.customer_id, str), f"customer_id powinno być str"
        assert isinstance(sample.date_sent, datetime), f"date_sent powinno być datetime, jest {type(sample.date_sent)}"
        
        print("  ✅ Typy poprawne")
        print()

def test_csv_writing():
    """Test zapisu obiektów do CSV."""
    print("=" * 60)
    print("TEST 2: Zapis obiektów do CSV")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    # Utwórz przykładowe obiekty
    test_samples = [
        SampleModel(
            id=100,
            customer_id="TEST_001",
            status="Sent",
            date_sent=datetime(2025, 11, 25),
            notes="Testowa próbka 1"
        ),
        SampleModel(
            id=101,
            customer_id="TEST_002",
            status="Draft",
            date_sent=datetime(2025, 11, 26),
            notes=None  # Opcjonalne pole
        )
    ]
    
    # Zapisz do pliku testowego
    test_file = Config.MOCK_DIR / "samples_test.csv"
    repo = CsvSampleRepository(test_file)
    
    print(f"\nZapisuję {len(test_samples)} próbek do {test_file}...")
    success = repo.save_samples(test_samples)
    
    if success:
        print("✅ Zapisano pomyślnie")
        
        # Odczytaj z powrotem i zweryfikuj
        print("\nOdczytuję z powrotem i weryfikuję...")
        repo2 = CsvSampleRepository(test_file)
        loaded_samples = repo2.load_all()
        
        print(f"Wczytano {len(loaded_samples)} próbek\n")
        
        for i, (original, loaded) in enumerate(zip(test_samples, loaded_samples), 1):
            print(f"Próbka {i}:")
            print(f"  Oryginał ID: {original.id}, Wczytany ID: {loaded.id}")
            print(f"  Oryginał date: {original.date_sent}, Wczytany date: {loaded.date_sent}")
            
            assert original.id == loaded.id, "ID się nie zgadza"
            assert original.date_sent == loaded.date_sent, "Data się nie zgadza"
            assert original.customer_id == loaded.customer_id, "Customer ID się nie zgadza"
            
            print("  ✅ Wszystkie pola się zgadzają")
            print()
        
        print("✅ Test zapisu i odczytu zakończony pomyślnie")
    else:
        print("❌ Błąd zapisu")

def show_csv_format():
    """Pokazuje poprawny format CSV dla SampleModel."""
    print("=" * 60)
    print("FORMAT CSV DLA SampleModel")
    print("=" * 60)
    
    print("""
Wymagane kolumny:
- id (int) - liczba całkowita
- customer_id (str) - string
- status (str) - string  
- date_sent (datetime) - data w formacie YYYY-MM-DD

Opcjonalne kolumny:
- notes (Optional[str]) - może być puste

Przykład poprawnego CSV:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
id;customer_id;status;date_sent;notes
1;CUST_001;Sent;2025-11-19;Próbki kawy arabica
2;CUST_002;Sent;2025-11-14;Próbki kawy robusta
3;CUST_003;Draft;2025-11-22;
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WAŻNE:
1. Separator: średnik (;)
2. Kodowanie: UTF-8 z BOM (utf-8-sig) - Excel automatycznie to używa
3. Format daty: YYYY-MM-DD (preferowany) lub DD.MM.YYYY
4. Puste opcjonalne pola: zostaw puste lub użyj wartości domyślnej
5. Nagłówki kolumn: muszą dokładnie odpowiadać nazwom pól w dataclass
    """)

if __name__ == "__main__":
    show_csv_format()
    print("\n")
    test_csv_reading()
    print("\n")
    test_csv_writing()

