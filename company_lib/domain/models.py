"""
Modele danych używane w aplikacji.
Używamy dataclasses dla prostoty i wydajności.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class NoteModel:
    """Model notatki z systemu ERP."""
    id: int
    customer_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    is_processed: bool = False
    
    def safe_content(self) -> str:
        """
        Zwraca content z zamienionymi znakami specjalnymi na bezpieczne odpowiedniki ASCII.
        Użyteczne do logowania.
        """
        return self.content.encode('ascii', 'replace').decode('ascii')

@dataclass
class SampleModel:
    """Model próbki wysłanej do klienta."""
    id: int
    customer_id: str
    status: str
    date_sent: datetime
    notes: Optional[str] = None

@dataclass
class CustomerModel:
    """Model klienta z systemu ERP."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    salesperson_email: Optional[str] = None  # Email sprzedawcy przypisanego do klienta
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TaskModel:
    """Model zadania dla sprzedawcy."""
    id: Optional[int] = None  # None dla nowych zadań
    customer_id: str = ""
    sample_id: int = 0
    task_type: str = "SAMPLE_FOLLOWUP"  # Typ zadania
    description: str = ""
    status: str = "PENDING"  # PENDING, COMPLETED, CANCELLED
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None  # Email sprzedawcy

@dataclass
class MailLogModel:
    """Model logu wysyłki maila."""
    id: Optional[int] = None  # None dla nowych logów
    to_email: str = ""
    subject: str = ""
    status: str = "PENDING"  # PENDING, SENT, FAILED
    error_message: Optional[str] = None  # Komunikat błędu jeśli status=FAILED
    sent_at: Optional[datetime] = None  # Data wysłania (jeśli status=SENT)
    created_at: datetime = field(default_factory=datetime.now)
    batch_id: Optional[str] = None  # ID partii wysyłki (np. dla grupowania)
    task_ids: Optional[str] = None  # Lista ID zadań (oddzielone przecinkami)

