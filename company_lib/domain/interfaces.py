"""
Interfejsy (ABC) dla repozytoriów.
Definiują kontrakt, który musi być spełniony przez wszystkie implementacje.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from company_lib.domain.models import NoteModel, SampleModel, CustomerModel, TaskModel, MailLogModel

class ICustomerRepository(ABC):
    """Interfejs repozytorium klientów."""
    
    @abstractmethod
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerModel]:
        """Pobiera klienta po ID."""
        pass
    
    @abstractmethod
    def get_customer_stats(self, customer_id: str) -> dict:
        """Pobiera statystyki klienta."""
        pass

class INoteRepository(ABC):
    """Interfejs repozytorium notatek."""
    
    @abstractmethod
    def get_all_notes(self, processed: Optional[bool] = None) -> List[NoteModel]:
        """Pobiera wszystkie notatki."""
        pass
    
    @abstractmethod
    def mark_as_processed(self, note_id: int, category: Optional[str] = None) -> bool:
        """Oznacza notatkę jako przetworzoną."""
        pass

class ISampleRepository(ABC):
    """Interfejs repozytorium próbek."""
    
    @abstractmethod
    def get_samples_by_status(self, status: str) -> List[SampleModel]:
        """Pobiera próbki po statusie."""
        pass

class ITaskRepository(ABC):
    """Interfejs repozytorium zadań."""
    
    @abstractmethod
    def get_tasks_by_customer_and_sample(self, customer_id: str, sample_id: int) -> List[TaskModel]:
        """Pobiera zadania dla konkretnego klienta i próbki."""
        pass
    
    @abstractmethod
    def create_task(self, task: TaskModel) -> TaskModel:
        """Tworzy nowe zadanie."""
        pass
    
    @abstractmethod
    def get_pending_tasks_by_salesperson(self, salesperson_email: str) -> List[TaskModel]:
        """Pobiera wszystkie oczekujące zadania dla sprzedawcy."""
        pass

class IMailLogRepository(ABC):
    """Interfejs repozytorium logów maili."""
    
    @abstractmethod
    def create_log(self, mail_log: MailLogModel) -> MailLogModel:
        """Tworzy nowy log wysyłki maila."""
        pass
    
    @abstractmethod
    def update_log_status(self, log_id: int, status: str, error_message: Optional[str] = None) -> bool:
        """Aktualizuje status logu."""
        pass
    
    @abstractmethod
    def get_last_failed_or_pending(self, batch_id: Optional[str] = None) -> Optional[MailLogModel]:
        """Pobiera ostatni nieudany lub oczekujący log (dla wznowienia wysyłki)."""
        pass
    
    @abstractmethod
    def get_logs_by_batch(self, batch_id: str) -> List[MailLogModel]:
        """Pobiera wszystkie logi dla danej partii wysyłki."""
        pass

