"""
Implementacje repozytoriów działające na plikach CSV.
Używane w fazie prototypowania i testach jednostkowych.
"""
import csv
from typing import Type, List, TypeVar, Optional, Dict, Any
from dataclasses import fields
from pathlib import Path
from datetime import datetime
from company_lib.domain.interfaces import (
    ICustomerRepository,
    INoteRepository,
    ISampleRepository,
    ITaskRepository,
    IMailLogRepository
)
from company_lib.domain.models import NoteModel, SampleModel, CustomerModel, TaskModel, MailLogModel
from company_lib.logger import setup_logger

logger = setup_logger("CSVRepositories")
T = TypeVar('T')

class CsvGenericRepository:
    """
    Generyczna klasa bazowa do czytania CSV i mapowania na modele.
    Automatycznie konwertuje typy na podstawie definicji dataclass.
    """
    
    def __init__(self, file_path: Path, model_cls: Type[T], delimiter: str = ';'):
        """
        Inicjalizuje repozytorium CSV.
        
        Args:
            file_path: Ścieżka do pliku CSV
            model_cls: Klasa modelu (NoteModel, SampleModel, etc.)
            delimiter: Separator w CSV (domyślnie ';' dla Excela)
        """
        self.file_path = file_path
        self.model_cls = model_cls
        self.delimiter = delimiter
        self._cache: Optional[List[T]] = None
    
    def load_all(self) -> List[T]:
        """
        Ładuje wszystkie rekordy z pliku CSV.
        
        Returns:
            Lista obiektów modelu
        """
        if self._cache is not None:
            return self._cache
        
        results = []
        try:
            # utf-8-sig usuwa BOM (krzaczki na początku pliku z Excela)
            with open(self.file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start od 2 (nagłówek to 1)
                    try:
                        # Konwertujemy surowy wiersz (strings) na typy z modelu
                        typed_data = self._map_row_to_types(row)
                        
                        # Sprawdź czy wszystkie wymagane pola są obecne
                        # Pole jest wymagane jeśli nie ma default i nie jest Optional
                        required_fields = []
                        for field_info in fields(self.model_cls):
                            # Sprawdź czy pole ma wartość domyślną
                            has_default = (
                                field_info.default is not field_info.default_factory
                                or (hasattr(field_info, 'default') and field_info.default is not None)
                                or (hasattr(field_info, 'default_factory') and field_info.default_factory is not None)
                            )
                            # Sprawdź czy pole jest opcjonalne
                            is_optional = (
                                hasattr(field_info.type, '__origin__') 
                                and field_info.type.__origin__ is type(None)
                            )
                            
                            if not has_default and not is_optional:
                                required_fields.append(field_info.name)
                        
                        missing_fields = [f for f in required_fields if f not in typed_data]
                        if missing_fields:
                            logger.warning(
                                f"Wiersz {row_num} w {self.file_path.name}: brakuje wymaganych pól: {missing_fields}. "
                                f"Pomijam wiersz."
                            )
                            continue
                        
                        results.append(self.model_cls(**typed_data))
                    except TypeError as e:
                        # Błąd przy tworzeniu obiektu - brakuje wymaganych argumentów
                        logger.warning(f"Błąd tworzenia obiektu z wiersza {row_num} w {self.file_path.name}: {e}")
                        logger.debug(f"Zawartość wiersza: {row}, typed_data: {typed_data if 'typed_data' in locals() else 'brak'}")
                        continue
                    except Exception as e:
                        logger.warning(f"Błąd parsowania wiersza {row_num} w {self.file_path.name}: {e}")
                        logger.debug(f"Zawartość wiersza: {row}")
                        continue
        except FileNotFoundError:
            logger.error(f"Nie znaleziono pliku: {self.file_path}")
            return []
        except Exception as e:
            logger.error(f"Błąd czytania pliku {self.file_path}: {e}")
            return []
        
        self._cache = results
        return results
    
    def _map_row_to_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Konwertuje stringi z CSV na typy zdefiniowane w dataclass.
        
        Args:
            row: Słownik z wartościami z CSV (wszystko jako string)
        
        Returns:
            Słownik z przekonwertowanymi wartościami
        """
        data = {}
        for field_info in fields(self.model_cls):
            name = field_info.name
            target_type = field_info.type
            value = row.get(name)
            
            if value is None or value == '':
                # Sprawdź czy pole jest opcjonalne (Optional[...])
                if hasattr(target_type, '__origin__') and target_type.__origin__ is type(None):
                    # Pole opcjonalne - ustaw None
                    data[name] = None
                    continue
                # Sprawdź czy pole ma wartość domyślną
                if hasattr(field_info, 'default') and field_info.default is not None:
                    continue  # Użyj wartości domyślnej
                elif hasattr(field_info, 'default_factory') and field_info.default_factory is not None:
                    continue  # Użyj factory
                else:
                    # Pole wymagane, ale brak wartości - pomiń to pole (może być błąd w danych)
                    continue
            
            # Konwersja typów
            try:
                if target_type == int:
                    data[name] = int(value)
                elif target_type == bool:
                    # Excel często zapisuje TRUE/FALSE albo 1/0
                    data[name] = value.lower() in ('true', '1', 'tak', 'yes', 't')
                elif target_type == datetime:
                    # Próbuj różne formaty daty
                    value_clean = value.strip()
                    for date_format in ['%Y-%m-%d', '%d.%m.%Y', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S']:
                        try:
                            data[name] = datetime.strptime(value_clean, date_format)
                            break
                        except ValueError:
                            continue
                    else:
                        # Jeśli żaden format nie pasuje
                        logger.warning(f"Nie można sparsować daty '{value}' dla pola {name}")
                        continue
                elif hasattr(target_type, '__origin__') and target_type.__origin__ is type(None):
                    # Optional[Type] - weź typ wewnętrzny
                    inner_type = target_type.__args__[0]
                    if inner_type == str:
                        data[name] = value
                    elif inner_type == int:
                        data[name] = int(value) if value else None
                    else:
                        data[name] = value
                else:
                    # String lub inny typ - zostaje jak jest
                    data[name] = value
            except (ValueError, TypeError) as e:
                logger.warning(f"Błąd konwersji wartości '{value}' dla pola {name} na typ {target_type}: {e}")
                continue
        
        return data
    
    def clear_cache(self):
        """Czyści cache, wymuszając ponowne odczytanie pliku."""
        self._cache = None
    
    def save_all(self, objects: List[T]) -> bool:
        """
        Zapisuje listę obiektów do pliku CSV.
        
        Args:
            objects: Lista obiektów modelu do zapisania
        
        Returns:
            True jeśli zapisano pomyślnie
        """
        try:
            # Tworzenie katalogu jeśli nie istnieje
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Pobierz nazwy pól z dataclass
            field_names = [field.name for field in fields(self.model_cls)]
            
            with open(self.file_path, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=field_names, delimiter=self.delimiter)
                writer.writeheader()
                
                for obj in objects:
                    row = {}
                    for field_name in field_names:
                        value = getattr(obj, field_name, None)
                        
                        # Konwersja wartości do formatu CSV
                        if value is None:
                            row[field_name] = ''
                        elif isinstance(value, datetime):
                            # Format daty: YYYY-MM-DD (standard ISO)
                            row[field_name] = value.strftime('%Y-%m-%d')
                        elif isinstance(value, bool):
                            # Boolean jako string
                            row[field_name] = 'True' if value else 'False'
                        else:
                            row[field_name] = str(value)
                    
                    writer.writerow(row)
            
            # Zaktualizuj cache
            self._cache = objects.copy()
            
            logger.info(f"Zapisano {len(objects)} obiektów do {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd zapisywania do {self.file_path}: {e}")
            return False


class CsvCustomerRepository(CsvGenericRepository, ICustomerRepository):
    """Repozytorium klientów działające na CSV."""
    
    def __init__(self, file_path: Path, note_repo=None, sample_repo=None):
        """
        Inicjalizuje repozytorium klientów.
        
        Args:
            file_path: Ścieżka do pliku CSV z klientami
            note_repo: Opcjonalne repozytorium notatek (do statystyk)
            sample_repo: Opcjonalne repozytorium próbek (do statystyk)
        """
        super().__init__(file_path, CustomerModel)
        self.customers = self.load_all()
        # Indeks dla szybkiego wyszukiwania
        self._by_id: Dict[str, CustomerModel] = {c.id: c for c in self.customers}
        self._note_repo = note_repo
        self._sample_repo = sample_repo
    
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerModel]:
        """Pobiera klienta po ID."""
        return self._by_id.get(customer_id)
    
    def get_customer_stats(self, customer_id: str) -> dict:
        """Pobiera statystyki klienta."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return {'notes_count': 0, 'samples_count': 0}
        
        # Liczenie statystyk jeśli mamy dostęp do innych repozytoriów
        notes_count = 0
        samples_count = 0
        
        if self._note_repo:
            all_notes = self._note_repo.get_all_notes()
            notes_count = sum(1 for n in all_notes if n.customer_id == customer_id)
        
        if self._sample_repo:
            all_samples = self._sample_repo.samples if hasattr(self._sample_repo, 'samples') else []
            samples_count = sum(1 for s in all_samples if s.customer_id == customer_id)
        
        return {
            'notes_count': notes_count,
            'samples_count': samples_count
        }


class CsvNoteRepository(CsvGenericRepository, INoteRepository):
    """Repozytorium notatek działające na CSV."""
    
    def __init__(self, file_path: Path):
        super().__init__(file_path, NoteModel)
        self.notes = self.load_all()
        self._processed_log: Dict[int, str] = {}  # note_id -> category
    
    def get_all_notes(self, processed: Optional[bool] = None) -> List[NoteModel]:
        """Pobiera wszystkie notatki z opcjonalnym filtrem."""
        if not self.notes:
            return []
        if processed is None:
            return self.notes.copy()
        else:
            return [n for n in self.notes if n.is_processed == processed]
    
    def mark_as_processed(self, note_id: int, category: Optional[str] = None) -> bool:
        """Oznacza notatkę jako przetworzoną (w pamięci)."""
        note = next((n for n in self.notes if n.id == note_id), None)
        if note:
            note.is_processed = True
            if category:
                self._processed_log[note_id] = category
            logger.info(f"[MOCK] Notatka {note_id} oznaczona jako przetworzona (kategoria: {category})")
            return True
        logger.warning(f"Nie znaleziono notatki o ID {note_id}")
        return False


class CsvSampleRepository(CsvGenericRepository, ISampleRepository):
    """Repozytorium próbek działające na CSV."""
    
    def __init__(self, file_path: Path):
        super().__init__(file_path, SampleModel)
        self.samples = self.load_all()
    
    def get_samples_by_status(self, status: str) -> List[SampleModel]:
        """Pobiera próbki po statusie."""
        if not self.samples:
            return []
        if not status:
            return []
        return [s for s in self.samples if s and s.status == status]
    
    def save_samples(self, samples: List[SampleModel]) -> bool:
        """
        Zapisuje listę próbek do CSV.
        
        Args:
            samples: Lista SampleModel do zapisania
        
        Returns:
            True jeśli zapisano pomyślnie
        """
        success = self.save_all(samples)
        if success:
            self.samples = samples.copy()
        return success


class CsvTaskRepository(ITaskRepository):
    """Repozytorium zadań działające na CSV z obsługą zapisu."""
    
    def __init__(self, file_path: Path):
        """
        Inicjalizuje repozytorium zadań.
        
        Args:
            file_path: Ścieżka do pliku CSV z zadaniami
        """
        self.file_path = file_path
        self.tasks: List[TaskModel] = []
        self._load_tasks()
        self._next_id = max([t.id for t in self.tasks if t.id], default=0) + 1
    
    def _load_tasks(self):
        """Ładuje zadania z pliku CSV."""
        if not self.file_path.exists():
            logger.info(f"Plik zadań nie istnieje, zostanie utworzony: {self.file_path}")
            self.tasks = []
            return
        
        try:
            with open(self.file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        task = TaskModel(
                            id=int(row.get('id', 0)) if row.get('id') else None,
                            customer_id=row.get('customer_id', ''),
                            sample_id=int(row.get('sample_id', 0)),
                            task_type=row.get('task_type', 'SAMPLE_FOLLOWUP'),
                            description=row.get('description', ''),
                            status=row.get('status', 'PENDING'),
                            created_at=datetime.strptime(row.get('created_at', ''), '%Y-%m-%d %H:%M:%S') if row.get('created_at') else datetime.now(),
                            assigned_to=row.get('assigned_to') if row.get('assigned_to') else None
                        )
                        self.tasks.append(task)
                    except Exception as e:
                        logger.warning(f"Błąd parsowania zadania: {e}, wiersz: {row}")
                        continue
        except Exception as e:
            logger.error(f"Błąd czytania pliku zadań {self.file_path}: {e}")
            self.tasks = []
    
    def _save_tasks(self):
        """Zapisuje zadania do pliku CSV."""
        try:
            # Tworzenie katalogu jeśli nie istnieje
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, mode='w', encoding='utf-8-sig', newline='') as f:
                fieldnames = ['id', 'customer_id', 'sample_id', 'task_type', 'description', 
                             'status', 'created_at', 'assigned_to']
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for task in self.tasks:
                    writer.writerow({
                        'id': task.id if task.id else '',
                        'customer_id': task.customer_id,
                        'sample_id': task.sample_id,
                        'task_type': task.task_type,
                        'description': task.description,
                        'status': task.status,
                        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'assigned_to': task.assigned_to if task.assigned_to else ''
                    })
            logger.debug(f"Zapisano {len(self.tasks)} zadań do {self.file_path}")
        except Exception as e:
            logger.error(f"Błąd zapisywania zadań do {self.file_path}: {e}")
            raise
    
    def get_tasks_by_customer_and_sample(self, customer_id: str, sample_id: int) -> List[TaskModel]:
        """Pobiera zadania dla konkretnego klienta i próbki."""
        return [t for t in self.tasks 
                if t.customer_id == customer_id and t.sample_id == sample_id]
    
    def create_task(self, task: TaskModel) -> TaskModel:
        """Tworzy nowe zadanie."""
        # Przypisz ID jeśli nie ma
        if task.id is None:
            task.id = self._next_id
            self._next_id += 1
        
        # Ustaw datę utworzenia jeśli nie ma
        if not task.created_at:
            task.created_at = datetime.now()
        
        self.tasks.append(task)
        self._save_tasks()
        logger.info(f"Utworzono zadanie ID: {task.id} dla klienta {task.customer_id}, próbka {task.sample_id}")
        return task
    
    def get_pending_tasks_by_salesperson(self, salesperson_email: str) -> List[TaskModel]:
        """Pobiera wszystkie oczekujące zadania dla sprzedawcy."""
        return [t for t in self.tasks 
                if t.assigned_to == salesperson_email and t.status == 'PENDING']


class CsvMailLogRepository(IMailLogRepository):
    """Repozytorium logów maili działające na CSV z obsługą zapisu."""
    
    def __init__(self, file_path: Path):
        """
        Inicjalizuje repozytorium logów maili.
        
        Args:
            file_path: Ścieżka do pliku CSV z logami
        """
        self.file_path = file_path
        self.logs: List[MailLogModel] = []
        self._load_logs()
        self._next_id = max([l.id for l in self.logs if l.id], default=0) + 1
    
    def _load_logs(self):
        """Ładuje logi z pliku CSV."""
        if not self.file_path.exists():
            logger.info(f"Plik z logami maili nie istnieje, zostanie utworzony: {self.file_path}")
            self.logs = []
            return
        
        try:
            with open(self.file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        # Parsowanie dat
                        created_at = datetime.strptime(row.get('created_at', ''), '%Y-%m-%d %H:%M:%S') if row.get('created_at') else datetime.now()
                        sent_at = datetime.strptime(row.get('sent_at', ''), '%Y-%m-%d %H:%M:%S') if row.get('sent_at') else None
                        
                        log = MailLogModel(
                            id=int(row.get('id', 0)) if row.get('id') else None,
                            to_email=row.get('to_email', ''),
                            subject=row.get('subject', ''),
                            status=row.get('status', 'PENDING'),
                            error_message=row.get('error_message') if row.get('error_message') else None,
                            sent_at=sent_at,
                            created_at=created_at,
                            batch_id=row.get('batch_id') if row.get('batch_id') else None,
                            task_ids=row.get('task_ids') if row.get('task_ids') else None
                        )
                        self.logs.append(log)
                    except Exception as e:
                        logger.warning(f"Błąd parsowania logu maila: {e}, wiersz: {row}")
                        continue
        except Exception as e:
            logger.error(f"Błąd czytania pliku z logami {self.file_path}: {e}")
            self.logs = []
    
    def _save_logs(self):
        """Zapisuje logi do pliku CSV."""
        try:
            # Tworzenie katalogu jeśli nie istnieje
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, mode='w', encoding='utf-8-sig', newline='') as f:
                fieldnames = ['id', 'to_email', 'subject', 'status', 'error_message', 
                             'sent_at', 'created_at', 'batch_id', 'task_ids']
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for log in self.logs:
                    writer.writerow({
                        'id': log.id if log.id else '',
                        'to_email': log.to_email,
                        'subject': log.subject,
                        'status': log.status,
                        'error_message': log.error_message if log.error_message else '',
                        'sent_at': log.sent_at.strftime('%Y-%m-%d %H:%M:%S') if log.sent_at else '',
                        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'batch_id': log.batch_id if log.batch_id else '',
                        'task_ids': log.task_ids if log.task_ids else ''
                    })
            logger.debug(f"Zapisano {len(self.logs)} logów maili do {self.file_path}")
        except Exception as e:
            logger.error(f"Błąd zapisywania logów do {self.file_path}: {e}")
            raise
    
    def create_log(self, mail_log: MailLogModel) -> MailLogModel:
        """Tworzy nowy log wysyłki maila."""
        # Przypisz ID jeśli nie ma
        if mail_log.id is None:
            mail_log.id = self._next_id
            self._next_id += 1
        
        # Ustaw datę utworzenia jeśli nie ma
        if not mail_log.created_at:
            mail_log.created_at = datetime.now()
        
        self.logs.append(mail_log)
        self._save_logs()
        logger.info(f"Utworzono log maila ID: {mail_log.id} dla {mail_log.to_email}, status: {mail_log.status}")
        return mail_log
    
    def update_log_status(self, log_id: int, status: str, error_message: Optional[str] = None) -> bool:
        """Aktualizuje status logu."""
        log = next((l for l in self.logs if l.id == log_id), None)
        if log:
            log.status = status
            if status == "SENT":
                log.sent_at = datetime.now()
                log.error_message = None
            elif status == "FAILED":
                log.error_message = error_message
            self._save_logs()
            logger.info(f"Zaktualizowano log maila ID: {log_id}, status: {status}")
            return True
        logger.warning(f"Nie znaleziono logu maila o ID {log_id}")
        return False
    
    def get_last_failed_or_pending(self, batch_id: Optional[str] = None) -> Optional[MailLogModel]:
        """
        Pobiera ostatni nieudany lub oczekujący log (dla wznowienia wysyłki).
        
        Args:
            batch_id: Opcjonalny ID partii - jeśli podany, szuka tylko w tej partii
        
        Returns:
            Ostatni log z statusem FAILED lub PENDING, None jeśli nie znaleziono
        """
        filtered_logs = self.logs
        if batch_id:
            filtered_logs = [l for l in self.logs if l.batch_id == batch_id]
        
        # Szukaj FAILED, potem PENDING
        failed_logs = [l for l in filtered_logs if l.status == "FAILED"]
        if failed_logs:
            # Sortuj po dacie utworzenia (najnowszy pierwszy)
            failed_logs.sort(key=lambda x: x.created_at, reverse=True)
            return failed_logs[0]
        
        pending_logs = [l for l in filtered_logs if l.status == "PENDING"]
        if pending_logs:
            pending_logs.sort(key=lambda x: x.created_at, reverse=True)
            return pending_logs[0]
        
        return None
    
    def get_logs_by_batch(self, batch_id: str) -> List[MailLogModel]:
        """Pobiera wszystkie logi dla danej partii wysyłki."""
        return [l for l in self.logs if l.batch_id == batch_id]

