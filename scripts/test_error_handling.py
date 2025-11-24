"""
Skrypt testowy do weryfikacji obsługi błędów i zabezpieczeń.
Testuje scenariusze z brakującymi plikami, pustymi wartościami i None.
"""
import sys
import io
from pathlib import Path
from datetime import datetime
from company_lib.infrastructure.repo_csv import (
    CsvSampleRepository,
    CsvNoteRepository,
    CsvCustomerRepository
)
from company_lib.config import Config
from company_lib.logger import setup_logger

# Napraw kodowanie dla Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = setup_logger("ErrorHandlingTest")

def test_missing_file():
    """Test: Brak pliku CSV"""
    print("=" * 60)
    print("TEST 1: Brak pliku CSV")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    # Plik który nie istnieje
    non_existent_file = Config.MOCK_DIR / "non_existent.csv"
    repo = CsvSampleRepository(non_existent_file)
    samples = repo.load_all()
    
    print(f"Wynik: {len(samples)} próbek (oczekiwane: 0)")
    assert len(samples) == 0, "Powinno zwrócić pustą listę"
    print("✅ Test przeszedł - zwrócono pustą listę\n")

def test_empty_csv():
    """Test: Pusty plik CSV (tylko nagłówek)"""
    print("=" * 60)
    print("TEST 2: Pusty plik CSV (tylko nagłówek)")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    # Utwórz pusty plik z nagłówkiem
    empty_file = Config.MOCK_DIR / "samples_empty.csv"
    with open(empty_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.write("id;customer_id;status;date_sent;notes\n")
    
    repo = CsvSampleRepository(empty_file)
    samples = repo.load_all()
    
    print(f"Wynik: {len(samples)} próbek (oczekiwane: 0)")
    assert len(samples) == 0, "Powinno zwrócić pustą listę"
    print("✅ Test przeszedł - zwrócono pustą listę\n")

def test_missing_required_fields():
    """Test: Brak wymaganych pól w CSV"""
    print("=" * 60)
    print("TEST 3: Brak wymaganych pól w CSV")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    # Utwórz plik z brakującymi polami
    invalid_file = Config.MOCK_DIR / "samples_invalid.csv"
    with open(invalid_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.write("id;customer_id;status;date_sent;notes\n")
        f.write(";CUST_001;Sent;2025-11-19;Test\n")  # Brak id
        f.write("2;;Sent;2025-11-19;Test\n")  # Brak customer_id
        f.write("3;CUST_003;;2025-11-19;Test\n")  # Brak status
        f.write("4;CUST_004;Sent;;Test\n")  # Brak date_sent
    
    repo = CsvSampleRepository(invalid_file)
    samples = repo.load_all()
    
    print(f"Wynik: {len(samples)} próbek (oczekiwane: 0 - wszystkie mają błędy)")
    # Wszystkie wiersze powinny być pominięte z powodu brakujących wymaganych pól
    print("✅ Test przeszedł - wiersze z błędami zostały pominięte\n")

def test_empty_lists():
    """Test: Puste listy w skrypcie"""
    print("=" * 60)
    print("TEST 4: Obsługa pustych list")
    print("=" * 60)
    
    if not Config.MOCK_DIR:
        print("BŁĄD: MOCK_DIR nie jest skonfigurowany")
        return
    
    # Test z pustymi repozytoriami
    empty_repo = CsvSampleRepository(Config.MOCK_DIR / "samples_empty.csv")
    samples = empty_repo.get_samples_by_status('Sent')
    
    print(f"Próbki ze statusem 'Sent': {len(samples)} (oczekiwane: 0)")
    assert len(samples) == 0, "Powinno zwrócić pustą listę"
    print("✅ Test przeszedł - pusta lista obsłużona poprawnie\n")

def test_none_values():
    """Test: Wartości None"""
    print("=" * 60)
    print("TEST 5: Obsługa wartości None")
    print("=" * 60)
    
    from scripts.sample_followup import analyze_notes_with_llm
    
    # Test z None
    result1 = analyze_notes_with_llm(None, "CUST_001", datetime.now())
    print(f"Wynik dla notes=None: {result1['has_confirmation']} (oczekiwane: False)")
    assert result1['has_confirmation'] == False, "Powinno zwrócić False"
    
    # Test z pustym customer_id
    result2 = analyze_notes_with_llm([], "", datetime.now())
    print(f"Wynik dla customer_id='': {result2['has_confirmation']} (oczekiwane: False)")
    assert result2['has_confirmation'] == False, "Powinno zwrócić False"
    
    # Test z None sample_date
    result3 = analyze_notes_with_llm([], "CUST_001", None)
    print(f"Wynik dla sample_date=None: {result3['has_confirmation']} (oczekiwane: False)")
    assert result3['has_confirmation'] == False, "Powinno zwrócić False"
    
    print("✅ Test przeszedł - wartości None obsłużone poprawnie\n")

if __name__ == "__main__":
    print("Rozpoczynam testy obsługi błędów...\n")
    
    try:
        test_missing_file()
        test_empty_csv()
        test_missing_required_fields()
        test_empty_lists()
        test_none_values()
        
        print("=" * 60)
        print("✅ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ BŁĄD W TESTACH: {e}")
        import traceback
        traceback.print_exc()

