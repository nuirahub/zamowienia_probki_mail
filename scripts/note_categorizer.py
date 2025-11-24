"""
Skrypt do kategoryzacji notatek używający logiki biznesowej z company_lib.
Używa fabryki repozytoriów - automatycznie wybiera CSV lub SQL na podstawie konfiguracji.
"""
from company_lib.core.logger import setup_logger
from company_lib.infrastructure.factories import get_note_repository
from company_lib.domain.erp_service import ERPService

def main():
    """Główna funkcja skryptu."""
    logger = setup_logger("NoteCategorizer")
    logger.info(">>> Start kategoryzacji notatek...")
    
    try:
        # Fabryka automatycznie wybiera CSV lub SQL na podstawie Config.USE_MOCK_DATA
        note_repo = get_note_repository()
        
        # Inicjalizacja serwisu ERP
        erp_service = ERPService(
            customer_repo=None,  # Można dodać jeśli potrzebne
            note_repo=note_repo
        )
            
            # Pobranie nieprzetworzonych notatek
            pending_notes = erp_service.get_pending_notes()
            logger.info(f"Znaleziono {len(pending_notes)} nieprzetworzonych notatek")
            
            # Przetwarzanie notatek
            for note in pending_notes:
                logger.info(f"Przetwarzanie notatki ID: {note.id}, Klient: {note.customer_id}")
                logger.debug(f"Treść: {note.safe_content()}")
                
                # TODO: Tutaj dodać logikę kategoryzacji (np. z użyciem LLM)
                # category = categorize_note(note.content)
                
                # Oznaczenie jako przetworzonej
                erp_service.process_note(note.id, category=None)
                logger.info(f"Notatka {note.id} oznaczona jako przetworzona")
        
        logger.info(">>> Kategoryzacja zakończona pomyślnie")
        
    except Exception as e:
        logger.error(f"Błąd podczas kategoryzacji: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

