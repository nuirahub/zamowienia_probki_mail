import csv
import os
import logging
import smtplib
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass, asdict

# --- KONFIGURACJA ---
CSV_FILE = "tasks_database.csv"
LOG_FILE = "process_log.log"
REMINDER_DAYS = 7
CSV_HEADERS = ["sample_id", "customer_id", "created_at", "status", "last_update"]

# --- KONFIGURACJA LOGOWANIA ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- 1. DEFINICJA WŁASNEGO WYJĄTKU ---
class NoDataFoundError(Exception):
    """Rzucany, gdy źródło danych zwróci None (np. błąd API/Bazy) zamiast listy."""
    pass

# --- 2. MODELE DANYCH (Data Classes) ---

@dataclass
class Sample:
    """Reprezentuje dane z zewnętrznego systemu próbek."""
    id: str
    customer_id: str
    status: str
    shipped_date: datetime

@dataclass
class Task:
    """
    Reprezentuje jeden wiersz w tabeli TASKS.
    To jest Twój model docelowy. Dzięki niemu kod biznesowy
    ma podpowiadanie składni (task.sample_id) zamiast task['sample_id'].
    """
    sample_id: str
    customer_id: str
    created_at: datetime
    status: str        # np. 'OPEN', 'REMINDED', 'CLOSED'
    last_update: datetime

# --- 3. MOCKI (Symulacja zewnętrznych systemów) ---

def get_samples_from_external_db() -> List[Sample]:
    """Symulacja pobierania danych. Może rzucić NoDataFoundError."""
    
    # SYMULACJA BŁĘDU: Odkomentuj linię poniżej, aby przetestować obsługę błędu
    # db_response = None 
    
    # SYMULACJA POPRAWNYCH DANYCH
    db_response = [
        {'id': 'SAMP_001', 'cust': 'CLIENT_A', 'status': 'Wysłane', 'date': '2023-10-20'},
        {'id': 'SAMP_002', 'cust': 'CLIENT_B', 'status': 'Wysłane', 'date': '2023-11-01'},
    ]

    if db_response is None:
        raise NoDataFoundError("Zewnętrzna baza próbek zwróciła wartość NULL.")

    # Mapowanie surowych danych na obiekty Sample
    samples = []
    for item in db_response:
        samples.append(Sample(
            id=item['id'],
            customer_id=item['cust'],
            status=item['status'],
            shipped_date=datetime.strptime(item['date'], "%Y-%m-%d")
        ))
    return samples

def check_llm_notes(customer_id: str, sample_id: str) -> bool:
    """Zwraca True jeśli LLM znajdzie potwierdzenie w notatce."""
    return False  # Symulacja: brak notatki

def send_email(to: str, subject: str, body: str):
    logging.info(f"📧 EMAIL do {to} | {subject}")

# --- 4. REPOZYTORIUM (Warstwa dostępu do danych) ---

class CsvTasksRepository:
    def __init__(self, filepath=CSV_FILE):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
            logging.info(f"Utworzono plik bazy: {self.filepath}")

    # --- METODY POMOCNICZE (SERIALIZACJA/DESERIALIZACJA) ---
    
    def _row_to_task(self, row: dict) -> Optional[Task]:
        """Konwertuje słownik z CSV na obiekt Task. Zwraca None, jeśli dane są uszkodzone."""
        try:
            return Task(
                sample_id=row['sample_id'],
                customer_id=row['customer_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                status=row['status'],
                last_update=datetime.fromisoformat(row['last_update'])
            )
        except (ValueError, KeyError, TypeError):
            logging.warning(f"Uszkodzony rekord w CSV dla ID: {row.get('sample_id', 'UNKNOWN')}")
            return None

    def _task_to_row(self, task: Task) -> dict:
        """Konwertuje obiekt Task na słownik do zapisu w CSV."""
        return {
            "sample_id": task.sample_id,
            "customer_id": task.customer_id,
            "created_at": task.created_at.isoformat(),
            "status": task.status,
            "last_update": task.last_update.isoformat()
        }

    # --- GŁÓWNE OPERACJE NA DANYCH ---

    def get_all_tasks(self) -> List[Task]:
        """
        Czyta plik i zwraca LISTĘ OBIEKTÓW typu Task.
        To jest kluczowa zmiana - pracujemy na typach, nie dictach.
        """
        tasks_objects = []
        try:
            with open(self.filepath, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    task_obj = self._row_to_task(row)
                    if task_obj:
                        tasks_objects.append(task_obj)
        except FileNotFoundError:
            logging.error("Plik bazy danych nie istnieje.")
            return []
        
        return tasks_objects

    def save_all_tasks(self, tasks: List[Task]):
        """Nadpisuje plik CSV listą obiektów Task."""
        try:
            with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                for task in tasks:
                    writer.writerow(self._task_to_row(task))
        except IOError as e:
            logging.error(f"Błąd zapisu bazy: {e}")

    def add_task(self, sample_id: str, customer_id: str):
        """Dodaje nowe zadanie (append) bez czytania całości."""
        new_task = Task(
            sample_id=sample_id,
            customer_id=customer_id,
            created_at=datetime.now(),
            status="OPEN",
            last_update=datetime.now()
        )
        try:
            with open(self.filepath, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if f.tell() == 0: writer.writeheader()
                writer.writerow(self._task_to_row(new_task))
            logging.info(f"Dodano zadanie: {sample_id}")
        except IOError as e:
            logging.error(f"Nie udało się dopisać zadania: {e}")

    def task_exists(self, sample_id: str) -> bool:
        # Optymalizacja: w małych plikach czytamy wszystko, w dużych bazach zrobisz SELECT count
        all_tasks = self.get_all_tasks()
        return any(t.sample_id == sample_id for t in all_tasks)

# --- 5. LOGIKA BIZNESOWA (FLOWS) ---

def process_new_samples(repo: CsvTasksRepository):
    logging.info("--- ETAP 1: Nowe Próbki ---")
    
    try:
        samples = get_samples_from_external_db()
        
        # Jeśli lista jest pusta (ale nie None), to po prostu return
        if not samples:
            logging.info("Brak nowych próbek.")
            return

        for sample in samples:
            try:
                if sample.status != "Wysłane":
                    continue
                
                if repo.task_exists(sample.id):
                    continue

                # Sprawdzenie LLM
                if check_llm_notes(sample.customer_id, sample.id):
                    logging.info(f"Znaleziono notatkę dla {sample.id}. Nie tworzę zadania.")
                else:
                    logging.info(f"Brak notatki dla {sample.id}. Tworzę zadanie.")
                    repo.add_task(sample.id, sample.customer_id)
                    send_email("opiekun@firma.pl", f"Nowe zadanie: {sample.id}", "Sprawdź status.")

            except Exception as e:
                logging.error(f"Błąd przetwarzania pojedynczej próbki {sample.id}: {e}")

    except NoDataFoundError as e:
        # TUTAJ ŁAPIEMY TWÓJ CUSTOMOWY BŁĄD
        logging.warning(f"⚠️ PRZERWANO ETAP 1: {e}. Przechodzę do następnego etapu.")
    
    except Exception as e:
        logging.error(f"Krytyczny błąd techniczny w ETAPIE 1: {e}")

def process_reminders(repo: CsvTasksRepository):
    logging.info("--- ETAP 2: Ponaglenia ---")
    
    # Pobieramy obiekty Task
    all_tasks = repo.get_all_tasks()
    if not all_tasks:
        return

    tasks_modified = False
    now = datetime.now()

    for task in all_tasks:
        # Tutaj działamy na obiekcie Task, a nie na słowniku!
        # Mamy dostęp do task.status zamiast task['status']
        
        if task.status == 'OPEN':
            delta = now - task.created_at
            if delta.days >= REMINDER_DAYS:
                try:
                    logging.info(f"Zadanie {task.sample_id} przeterminowane ({delta.days} dni). Wysyłam maila.")
                    send_email(
                        "opiekun@firma.pl", 
                        f"PONAGLENIE: {task.sample_id}", 
                        "Zadanie wisi od tygodnia."
                    )
                    
                    # Aktualizujemy stan obiektu
                    task.status = 'REMINDED'
                    task.last_update = now
                    tasks_modified = True
                    
                except Exception as e:
                    logging.error(f"Błąd wysyłki maila dla {task.sample_id}: {e}")

    # Jeśli zmieniliśmy jakieś statusy, zapisujemy całość do pliku
    if tasks_modified:
        repo.save_all_tasks(all_tasks)
        logging.info("Zaktualizowano plik bazy danych po wysyłce ponagleń.")
    else:
        logging.info("Brak zmian w statusach zadań.")

# --- 6. GŁÓWNY ORCHESTRATOR ---

def main():
    logging.info("START AUTOMATU")
    
    try:
        repo = CsvTasksRepository()
    except Exception as e:
        logging.critical(f"Nie można uruchomić repozytorium: {e}")
        return

    # Uruchomienie niezależnych procesów
    process_new_samples(repo)
    process_reminders(repo)

    logging.info("KONIEC PRACY")

if __name__ == "__main__":
    main()