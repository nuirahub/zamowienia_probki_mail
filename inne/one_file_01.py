import csv
import os
import logging
import smtplib  # Do ewentualnej wysyłki maili
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# --- KONFIGURACJA ---
CSV_FILE = "tasks_database.csv"
LOG_FILE = "process_log.log"
REMINDER_DAYS = 7  # Po ilu dniach wysłać ponaglenie
CSV_HEADERS = ["sample_id", "customer_id", "created_at", "status", "last_update"]

# --- LOGOWANIE ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- MODELE DANYCH ---
@dataclass
class Sample:
    id: str
    customer_id: str
    status: str
    shipped_date: datetime

# --- MOCKI (ZAŚLEPKI) ---
# Tutaj wstawisz swoje faktyczne funkcje łączące się z bazą SQL i LLM
def get_samples_from_external_db(days_back=14) -> List[Sample]:
    """Symulacja pobierania danych z zewnętrznego systemu."""
    # Przykład danych
    return [
        Sample(id="SAMPLE_001", customer_id="CUST_A", status="Wysłane", shipped_date=datetime.now() - timedelta(days=2)),
        Sample(id="SAMPLE_002", customer_id="CUST_B", status="Wysłane", shipped_date=datetime.now() - timedelta(days=10)),
    ]

def check_llm_notes(customer_id: str, sample_id: str) -> bool:
    """Symulacja LLM. Zwraca True, jeśli klient potwierdził odbiór w notatce."""
    return False  # Domyślnie: brak potwierdzenia

def send_email(to_user: str, subject: str, body: str):
    """Symulacja wysyłki maila."""
    logging.info(f"[MAIL] Do: {to_user} | Temat: {subject}")

# --- REPOZYTORIUM CSV (Serce operacji na plikach) ---
class CsvTasksRepository:
    def __init__(self, filepath=CSV_FILE):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Tworzy plik z nagłówkami, jeśli nie istnieje."""
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(CSV_HEADERS)
                logging.info(f"Utworzono nowy plik bazy danych: {self.filepath}")
            except IOError as e:
                logging.critical(f"Nie można utworzyć pliku CSV! {e}")
                raise

    def _read_all_tasks(self) -> List[Dict]:
        """Pomocnicza: czyta cały plik do pamięci."""
        tasks = []
        try:
            with open(self.filepath, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tasks.append(row)
        except FileNotFoundError:
            logging.error("Plik CSV zniknął w trakcie pracy.")
            return []
        return tasks

    def _save_all_tasks(self, tasks: List[Dict]):
        """Pomocnicza: nadpisuje plik nową listą zadań."""
        try:
            with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(tasks)
        except IOError as e:
            logging.error(f"Błąd zapisu do CSV: {e}")

    def task_exists(self, sample_id: str) -> bool:
        tasks = self._read_all_tasks()
        for task in tasks:
            if task['sample_id'] == sample_id:
                return True
        return False

    def add_task(self, sample_id: str, customer_id: str):
        # Tryb 'a' (append) jest bezpieczniejszy niż nadpisywanie całości
        try:
            with open(self.filepath, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                # Sprawdzamy czy plik nie jest pusty (np. ktoś usunął nagłówki)
                if f.tell() == 0:
                    writer.writeheader()
                
                writer.writerow({
                    "sample_id": sample_id,
                    "customer_id": customer_id,
                    "created_at": datetime.now().isoformat(),
                    "status": "OPEN",
                    "last_update": datetime.now().isoformat()
                })
            logging.info(f"Dodano zadanie do CSV: {sample_id}")
        except IOError as e:
            logging.error(f"Nie udało się dopisać zadania: {e}")

    def get_overdue_tasks(self) -> List[Dict]:
        """Zwraca listę zadań, które są OPEN i starsze niż REMINDER_DAYS."""
        tasks = self._read_all_tasks()
        overdue = []
        now = datetime.now()

        for task in tasks:
            # Walidacja struktury wiersza
            if 'status' not in task or 'created_at' not in task:
                continue 
            
            if task['status'] == 'OPEN':
                try:
                    # Parsowanie daty
                    created_at = datetime.fromisoformat(task['created_at'])
                    if (now - created_at).days >= REMINDER_DAYS:
                        overdue.append(task)
                except ValueError:
                    logging.warning(f"Uszkodzona data w rekordzie {task.get('sample_id')}. Pomijam.")
        return overdue

    def update_task_status(self, sample_id: str, new_status: str):
        """W CSV musimy odczytać całość, zmienić w pamięci i zapisać całość."""
        tasks = self._read_all_tasks()
        updated = False
        
        for task in tasks:
            if task['sample_id'] == sample_id:
                task['status'] = new_status
                task['last_update'] = datetime.now().isoformat()
                updated = True
                break # Zakładamy unikalność ID, więc kończymy pętlę
        
        if updated:
            self._save_all_tasks(tasks)
            logging.info(f"Zaktualizowano status {sample_id} na {new_status}")

# --- FLOW 1: TWORZENIE NOWYCH ZADAŃ ---
def process_new_samples(repo: CsvTasksRepository):
    logging.info("--- ETAP 1: Sprawdzanie nowych próbek ---")
    
    try:
        samples = get_samples_from_external_db()
    except Exception as e:
        logging.error(f"Błąd połączenia ze źródłem próbek: {e}")
        return # Early return - nie ma danych, wychodzimy

    if not samples:
        logging.info("Brak próbek do przetworzenia.")
        return

    for sample in samples:
        try:
            # Logika biznesowa
            if sample.status != "Wysłane":
                continue
                
            if repo.task_exists(sample.id):
                continue # Już obsłużone

            # Sprawdzenie LLM
            is_resolved = check_llm_notes(sample.customer_id, sample.id)
            
            if is_resolved:
                logging.info(f"Próbka {sample.id} potwierdzona (LLM). Pomijam tworzenie zadania.")
                # Opcjonalnie: można dodać do CSV jako CLOSED, żeby nie pytać LLM ponownie
            else:
                logging.info(f"Brak potwierdzenia dla {sample.id}. Tworzę zadanie.")
                repo.add_task(sample.id, sample.customer_id)
                send_email("opiekun@firma.pl", f"Monitoruj próbkę {sample.id}", "Wysłano próbkę, brak potwierdzenia.")

        except Exception as e:
            logging.error(f"Błąd przy przetwarzaniu próbki {sample.id}: {e}")
            # Continue działa tu automatycznie, pętla idzie dalej

# --- FLOW 2: PONAGLENIA (MAINTENANCE) ---
def process_reminders(repo: CsvTasksRepository):
    logging.info("--- ETAP 2: Weryfikacja zaległości (CSV) ---")
    
    # Nie używamy try-except na całość, bo metoda get_overdue_tasks jest bezpieczna
    overdue_tasks = repo.get_overdue_tasks()

    if not overdue_tasks:
        logging.info("Brak zaległych zadań.")
        return

    for task in overdue_tasks:
        sample_id = task['sample_id']
        try:
            logging.info(f"Wysyłam ponaglenie dla zadania: {sample_id}")
            
            # Wysłanie maila
            send_email(
                "opiekun@firma.pl", 
                f"PONAGLENIE: Próbka {sample_id}", 
                "Minął tydzień, a status jest nadal otwarty."
            )
            
            # Aktualizacja w CSV
            repo.update_task_status(sample_id, "REMINDED")
            
        except Exception as e:
            logging.error(f"Nie udało się wysłać ponaglenia dla {sample_id}: {e}")

# --- GŁÓWNY ORCHESTRATOR ---
def main():
    logging.info("URUCHOMIENIE AUTOMATU")
    
    # 1. Inicjalizacja Repozytorium (tworzy plik CSV jeśli brak)
    try:
        repo = CsvTasksRepository()
    except Exception as e:
        logging.critical("Błąd krytyczny inicjalizacji CSV. Stop.")
        return

    # 2. Uruchomienie obu procesów niezależnie
    # Błąd w jednym nie zatrzymuje drugiego
    
    try:
        process_new_samples(repo)
    except Exception as e:
        logging.error(f"Krytyczny błąd w ETAPIE 1: {e}", exc_info=True)

    try:
        process_reminders(repo)
    except Exception as e:
        logging.error(f"Krytyczny błąd w ETAPIE 2: {e}", exc_info=True)

    logging.info("KONIEC PRACY")

if __name__ == "__main__":
    main()