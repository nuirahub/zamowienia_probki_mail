"""
Skrypt do monitoringu danych klienta.
Pobiera informacje o kliencie wraz ze statystykami.
Używa fabryki repozytoriów - automatycznie wybiera CSV lub SQL na podstawie konfiguracji.
"""
from company_lib.core.logger import setup_logger
from company_lib.infrastructure.factories import get_all_repositories
from company_lib.domain.erp_service import ERPService

def main():
    """Główna funkcja skryptu."""
    logger = setup_logger("CustomerMonitor")
    logger.info(">>> Rozpoczynam monitoring klientów...")
    
    try:
        # Fabryka automatycznie wybiera CSV lub SQL na podstawie Config.USE_MOCK_DATA
        # get_all_repositories() zapewnia, że w trybie CSV statystyki działają poprawnie
        customer_repo, note_repo, sample_repo = get_all_repositories()
        
        # Inicjalizacja serwisu ERP
        erp_service = ERPService(
            customer_repo=customer_repo,
            note_repo=note_repo
        )
            
            # TODO: Tutaj można dodać logikę pobierania listy klientów do monitorowania
            # Na przykład z pliku konfiguracyjnego lub z bazy danych
            # customer_ids = get_customers_to_monitor()
            
            # Przykładowe użycie - monitoring konkretnego klienta
            # W rzeczywistości można iterować po liście klientów
            example_customer_id = "CUST_001"  # Przykładowe ID
            
            logger.info(f"Monitorowanie klienta: {example_customer_id}")
            
            customer_data = erp_service.get_customer_with_stats(example_customer_id)
            
            if customer_data:
                customer = customer_data['customer']
                stats = customer_data['stats']
                
                logger.info(f"Klient: {customer.name} (ID: {customer.id})")
                logger.info(f"Email: {customer.email or 'Brak'}")
                logger.info(f"Telefon: {customer.phone or 'Brak'}")
                logger.info(f"Statystyki:")
                logger.info(f"  - Liczba notatek: {stats['notes_count']}")
                logger.info(f"  - Liczba próbek: {stats['samples_count']}")
            else:
                logger.warning(f"Nie znaleziono klienta o ID: {example_customer_id}")
            
            # Pobranie nieprzetworzonych notatek dla wszystkich klientów
            pending_notes = erp_service.get_pending_notes()
            logger.info(f"Znaleziono {len(pending_notes)} nieprzetworzonych notatek")
            
            # Grupowanie notatek po kliencie
            notes_by_customer = {}
            for note in pending_notes:
                if note.customer_id not in notes_by_customer:
                    notes_by_customer[note.customer_id] = []
                notes_by_customer[note.customer_id].append(note)
            
            # Raportowanie
            logger.info("Raport nieprzetworzonych notatek:")
            for customer_id, notes in notes_by_customer.items():
                logger.info(f"  Klient {customer_id}: {len(notes)} notatek")
        
        logger.info(">>> Monitoring zakończony pomyślnie")
        
    except Exception as e:
        logger.error(f"Błąd podczas monitoringu: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

