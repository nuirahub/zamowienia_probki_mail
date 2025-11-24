"""
Serwis ERP - logika biznesowa operująca na repozytoriach.
Używa interfejsów, więc działa zarówno z SQL jak i CSV repozytoriami.
"""
from typing import List, Optional
from company_lib.domain.models import NoteModel, CustomerModel
from company_lib.domain.interfaces import (
    ICustomerRepository,
    INoteRepository,
    ISampleRepository
)
from company_lib.logger import setup_logger

logger = setup_logger("ERPService")

class ERPService:
    """
    Główny serwis ERP łączący logikę biznesową z repozytoriami.
    Działa z dowolną implementacją interfejsów (SQL lub CSV).
    """
    
    def __init__(
        self,
        customer_repo: Optional[ICustomerRepository],
        note_repo: INoteRepository,
        sample_repo: Optional[ISampleRepository] = None
    ):
        """
        Inicjalizuje serwis z repozytoriami.
        
        Args:
            customer_repo: Repozytorium klientów
            note_repo: Repozytorium notatek
            sample_repo: Repozytorium próbek (opcjonalne)
        """
        self.customer_repo = customer_repo
        self.note_repo = note_repo
        self.sample_repo = sample_repo
    
    def get_customer_with_stats(self, customer_id: str) -> Optional[dict]:
        """
        Pobiera klienta wraz ze statystykami.
        
        Args:
            customer_id: ID klienta
        
        Returns:
            Słownik z danymi klienta i statystykami lub None
        """
        customer = self.customer_repo.get_customer_by_id(customer_id)
        if not customer:
            return None
        
        stats = self.customer_repo.get_customer_stats(customer_id)
        
        return {
            'customer': customer,
            'stats': stats
        }
    
    def get_pending_notes(self) -> List[NoteModel]:
        """
        Pobiera nieprzetworzone notatki.
        
        Returns:
            Lista nieprzetworzonych notatek
        """
        return self.note_repo.get_all_notes(processed=False)
    
    def process_note(self, note_id: int, category: Optional[str] = None) -> bool:
        """
        Przetwarza notatkę (oznacza jako przetworzoną).
        
        Args:
            note_id: ID notatki
            category: Opcjonalna kategoria
        
        Returns:
            True jeśli przetworzono pomyślnie
        """
        return self.note_repo.mark_as_processed(note_id, category)

