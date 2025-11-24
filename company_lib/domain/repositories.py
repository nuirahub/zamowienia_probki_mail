"""
Repozytoria do dostępu do danych (implementacja SQL).
Używają dependency injection - połączenie do bazy przekazywane jest w konstruktorze.
Implementują interfejsy z domain.interfaces.
"""
from typing import List, Optional
from company_lib.domain.interfaces import (
    ICustomerRepository,
    INoteRepository,
    ISampleRepository
)
from company_lib.domain.models import NoteModel, SampleModel, CustomerModel
from company_lib.core.database import MSSQLConnection
from company_lib.logger import setup_logger

logger = setup_logger("Repositories")

class CustomerRepository(ICustomerRepository):
    """
    Repozytorium do operacji na klientach.
    """
    
    def __init__(self, db_connection: MSSQLConnection):
        """
        Inicjalizuje repozytorium z połączeniem do bazy.
        
        Args:
            db_connection: Instancja MSSQLConnection
        """
        self.db = db_connection
    
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerModel]:
        """
        Pobiera klienta po ID.
        
        Args:
            customer_id: ID klienta
        
        Returns:
            CustomerModel lub None jeśli nie znaleziono
        """
        query = """
            SELECT Id, Name, Email, Phone, CreatedAt
            FROM ERP.dbo.Customers
            WHERE Id = ?
        """
        try:
            result = self.db.execute_query(query, (customer_id,))
            if result:
                row = result[0]
                return CustomerModel(
                    id=row[0],
                    name=row[1],
                    email=row[2],
                    phone=row[3],
                    created_at=row[4] if len(row) > 4 else None
                )
            return None
        except Exception as e:
            logger.error(f"Błąd pobierania klienta {customer_id}: {e}")
            return None
    
    def get_customer_stats(self, customer_id: str) -> dict:
        """
        Pobiera statystyki klienta.
        
        Args:
            customer_id: ID klienta
        
        Returns:
            Słownik ze statystykami
        """
        query = """
            SELECT 
                COUNT(DISTINCT n.Id) as NotesCount,
                COUNT(DISTINCT s.Id) as SamplesCount
            FROM ERP.dbo.Customers c
            LEFT JOIN ERP.dbo.Notes n ON n.CustomerId = c.Id
            LEFT JOIN ERP.dbo.Samples s ON s.CustomerId = c.Id
            WHERE c.Id = ?
        """
        try:
            result = self.db.execute_query(query, (customer_id,))
            if result:
                row = result[0]
                return {
                    'notes_count': row[0] or 0,
                    'samples_count': row[1] or 0
                }
            return {'notes_count': 0, 'samples_count': 0}
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk klienta {customer_id}: {e}")
            return {'notes_count': 0, 'samples_count': 0}

class NoteRepository(INoteRepository):
    """
    Repozytorium do operacji na notatkach.
    """
    
    def __init__(self, db_connection: MSSQLConnection):
        """
        Inicjalizuje repozytorium z połączeniem do bazy.
        
        Args:
            db_connection: Instancja MSSQLConnection
        """
        self.db = db_connection
    
    def get_all_notes(self, processed: Optional[bool] = None) -> List[NoteModel]:
        """
        Pobiera wszystkie notatki.
        
        Args:
            processed: Filtr po statusie przetworzenia (None = wszystkie)
        
        Returns:
            Lista NoteModel
        """
        if processed is None:
            query = "SELECT Id, CustomerId, NoteContent, CreatedAt, Processed FROM ERP.dbo.Notes"
            params = None
        else:
            query = "SELECT Id, CustomerId, NoteContent, CreatedAt, Processed FROM ERP.dbo.Notes WHERE Processed = ?"
            params = (1 if processed else 0,)
        
        try:
            results = self.db.execute_query(query, params)
            notes = []
            for row in results:
                notes.append(NoteModel(
                    id=row[0],
                    customer_id=row[1],
                    content=row[2],
                    created_at=row[3] if len(row) > 3 else None,
                    is_processed=bool(row[4]) if len(row) > 4 else False
                ))
            return notes
        except Exception as e:
            logger.error(f"Błąd pobierania notatek: {e}")
            return []
    
    def mark_as_processed(self, note_id: int, category: Optional[str] = None) -> bool:
        """
        Oznacza notatkę jako przetworzoną.
        
        Args:
            note_id: ID notatki
            category: Opcjonalna kategoria
        
        Returns:
            True jeśli zaktualizowano pomyślnie
        """
        query = "UPDATE ERP.dbo.Notes SET Processed = 1 WHERE Id = ?"
        try:
            self.db.execute_non_query(query, (note_id,))
            logger.info(f"Notatka {note_id} oznaczona jako przetworzona")
            return True
        except Exception as e:
            logger.error(f"Błąd aktualizacji notatki {note_id}: {e}")
            return False

class SampleRepository(ISampleRepository):
    """
    Repozytorium do operacji na próbkach.
    """
    
    def __init__(self, db_connection: MSSQLConnection):
        """
        Inicjalizuje repozytorium z połączeniem do bazy.
        
        Args:
            db_connection: Instancja MSSQLConnection
        """
        self.db = db_connection
    
    def get_samples_by_status(self, status: str) -> List[SampleModel]:
        """
        Pobiera próbki po statusie.
        
        Args:
            status: Status próbki (np. 'Sent')
        
        Returns:
            Lista SampleModel
        """
        query = """
            SELECT Id, CustomerId, Status, DateSent, Notes
            FROM ERP.dbo.Samples
            WHERE Status = ?
        """
        try:
            results = self.db.execute_query(query, (status,))
            samples = []
            for row in results:
                samples.append(SampleModel(
                    id=row[0],
                    customer_id=row[1],
                    status=row[2],
                    date_sent=row[3],
                    notes=row[4] if len(row) > 4 else None
                ))
            return samples
        except Exception as e:
            logger.error(f"Błąd pobierania próbek: {e}")
            return []

