"""
Skrypt do monitorowania próbek i tworzenia zadań dla sprzedawców.
Sprawdza próbki z ostatnich 14 dni i weryfikuje czy:
1. Istnieje zadanie w TASKS dla tej próbki
2. Czy w notatkach jest potwierdzenie otrzymania próbki
Jeśli nie ma ani zadania ani potwierdzenia, tworzy zadanie i wysyła email.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from company_lib.logger import setup_logger
from company_lib.infrastructure.factories import get_all_repositories
from company_lib.infrastructure.repo_csv import CsvTaskRepository, CsvMailLogRepository
from company_lib.domain.models import TaskModel
from company_lib.core.mailer import Mailer
from company_lib.core.llm_service import LLMService
from company_lib.config import Config
import uuid

logger = setup_logger("SampleFollowup")

def analyze_notes_with_llm(notes: List, customer_id: str, sample_date: datetime, llm_provider: str = None) -> Dict[str, Any]:
    """
    Analizuje notatki używając LLM (Gemini, OpenAI lub Qwen) do sprawdzenia statusu próbki.
    
    Args:
        notes: Lista notatek (może być pusta lub None)
        customer_id: ID klienta (nie może być None ani pusty)
        sample_date: Data wysłania próbki (nie może być None)
        llm_provider: Nazwa dostawcy LLM ("gemini", "openai", "qwen") lub None dla domyślnego z Config
    
    Returns:
        Słownik z wynikami analizy
    """
    # Walidacja wejściowa
    if notes is None:
        logger.warning("Lista notatek jest None, zwracam pusty wynik")
        return {
            "has_confirmation": False,
            "sample_received": False,
            "has_delay": False,
            "customer_satisfied": None,
            "best_note_analysis": None,
            "all_analyses": []
        }
    
    if not customer_id:
        logger.warning("customer_id jest pusty, zwracam pusty wynik")
        return {
            "has_confirmation": False,
            "sample_received": False,
            "has_delay": False,
            "customer_satisfied": None,
            "best_note_analysis": None,
            "all_analyses": []
        }
    
    if sample_date is None:
        logger.warning("sample_date jest None, zwracam pusty wynik")
        return {
            "has_confirmation": False,
            "sample_received": False,
            "has_delay": False,
            "customer_satisfied": None,
            "best_note_analysis": None,
            "all_analyses": []
        }
    """
    Analizuje notatki używając LLM (Gemini, OpenAI lub Qwen) do sprawdzenia statusu próbki.
    
    Args:
        notes: Lista notatek
        customer_id: ID klienta
        sample_date: Data wysłania próbki
        llm_provider: Nazwa dostawcy LLM ("gemini", "openai", "qwen") lub None dla domyślnego z Config
    
    Returns:
        Słownik z wynikami analizy:
        {
            "has_confirmation": bool,  # Czy jest potwierdzenie otrzymania
            "sample_received": bool,  # Czy próbka dotarła
            "has_delay": bool,  # Czy jest opóźnienie
            "customer_satisfied": Optional[bool],  # Czy klient jest zadowolony
            "best_note_analysis": Dict,  # Analiza najlepszej notatki
            "all_analyses": List[Dict]  # Wszystkie analizy
        }
    """
    try:
        llm_client = LLMService.get_client(llm_provider)
        provider_name = llm_provider or Config.LLM_PROVIDER
        logger.info(f"Używam {provider_name} do analizy notatek")
    except Exception as e:
        logger.error(f"Nie można zainicjalizować klienta LLM: {e}")
        # Fallback do prostej weryfikacji
        return {
            "has_confirmation": False,
            "sample_received": False,
            "has_delay": False,
            "customer_satisfied": None,
            "best_note_analysis": None,
            "all_analyses": []
        }
    
    # Filtruj notatki dla tego klienta po dacie wysłania próbki
    relevant_notes = [
        note for note in notes
        if note.customer_id == customer_id and note.created_at >= sample_date
    ]
    
    if not relevant_notes:
        logger.debug(f"Brak notatek dla klienta {customer_id} po dacie {sample_date.date()}")
        return {
            "has_confirmation": False,
            "sample_received": False,
            "has_delay": False,
            "customer_satisfied": None,
            "best_note_analysis": None,
            "all_analyses": []
        }
    
    provider_name = llm_provider or Config.LLM_PROVIDER
    logger.info(f"Analizuję {len(relevant_notes)} notatek dla klienta {customer_id} używając {provider_name}")
    
    # Analizuj każdą notatkę
    all_analyses = []
    sample_date_str = sample_date.strftime('%Y-%m-%d')
    
    for note in relevant_notes:
        # Walidacja notatki
        if not note or not hasattr(note, 'content'):
            logger.warning(f"Nieprawidłowa notatka w liście, pomijam")
            continue
        
        if not note.content or not note.content.strip():
            logger.debug(f"Notatka ID {note.id} ma pustą treść, pomijam")
            continue
        
        try:
            logger.debug(f"Analizuję notatkę ID {note.id}: {note.content[:50]}...")
            analysis = llm_client.analyze_note_for_sample(note.content, sample_date_str)
            analysis['note_id'] = note.id
            analysis['note_content'] = note.content[:100]  # Krótki fragment dla logowania
            all_analyses.append(analysis)
        except Exception as e:
            logger.error(f"Błąd analizy notatki ID {note.id}: {e}")
            continue
    
    # Znajdź najlepszą notatkę (najwyższa pewność + mentions_sample=True)
    best_analysis = None
    best_confidence = 0.0
    
    for analysis in all_analyses:
        if analysis.get('mentions_sample') and analysis.get('confidence', 0) > best_confidence:
            best_confidence = analysis['confidence']
            best_analysis = analysis
    
    # Podsumowanie wyników
    has_confirmation = False
    sample_received = False
    has_delay = False
    customer_satisfied = None
    
    if best_analysis:
        has_confirmation = best_analysis.get('mentions_sample', False)
        status = best_analysis.get('sample_status', 'unknown')
        sample_received = (status == 'received')
        has_delay = (status == 'delayed')
        
        satisfaction = best_analysis.get('customer_satisfaction', 'unknown')
        if satisfaction == 'satisfied':
            customer_satisfied = True
        elif satisfaction == 'unsatisfied':
            customer_satisfied = False
        else:
            customer_satisfied = None
        
        provider_name = llm_provider or Config.LLM_PROVIDER
        logger.info(
            f"Wynik analizy {provider_name} dla klienta {customer_id}: "
            f"status={status}, satisfaction={satisfaction}, confidence={best_confidence:.2f}"
        )
    
    return {
        "has_confirmation": has_confirmation,
        "sample_received": sample_received,
        "has_delay": has_delay,
        "customer_satisfied": customer_satisfied,
        "best_note_analysis": best_analysis,
        "all_analyses": all_analyses
    }

def main():
    """Główna funkcja skryptu."""
    logger.info(">>> Rozpoczynam monitorowanie próbek i tworzenie zadań...")
    
    try:
        # Pobranie repozytoriów
        customer_repo, note_repo, sample_repo = get_all_repositories()
        
        # Inicjalizacja repozytoriów
        if not Config.MOCK_DIR:
            raise ValueError("MOCK_DIR nie jest skonfigurowany")
        task_repo = CsvTaskRepository(Config.MOCK_DIR / "tasks.csv")
        mail_log_repo = CsvMailLogRepository(Config.MOCK_DIR / "mail_logs.csv")
        
        # Inicjalizacja mailera z repozytorium logów
        mailer = Mailer(mail_log_repo=mail_log_repo)
        
        # Generuj unikalny batch_id dla tej sesji wysyłki
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Batch ID dla tej sesji: {batch_id}")
        
        # Sprawdź czy są nieudane lub oczekujące maile z poprzednich sesji
        last_failed_log = mail_log_repo.get_last_failed_or_pending()
        retry_emails = {}  # Mapa: email -> log do ponowienia
        
        if last_failed_log:
            logger.warning(
                f"Znaleziono nieudany/oczekujący mail z poprzedniej sesji: "
                f"ID={last_failed_log.id}, to={last_failed_log.to_email}, "
                f"status={last_failed_log.status}, batch={last_failed_log.batch_id}"
            )
            if last_failed_log.batch_id:
                # Pobierz wszystkie logi z tego batcha
                batch_logs = mail_log_repo.get_logs_by_batch(last_failed_log.batch_id)
                logger.info(f"Znaleziono {len(batch_logs)} logów w batchu {last_failed_log.batch_id}")
                
                # Stwórz mapę: email -> ostatni log (FAILED lub PENDING)
                for log in batch_logs:
                    if log.status in ["FAILED", "PENDING"]:
                        if log.to_email not in retry_emails or log.created_at > retry_emails[log.to_email].created_at:
                            retry_emails[log.to_email] = log
                
                logger.info(f"Znaleziono {len(retry_emails)} emaili do ponownej próby wysyłki")
                # Użyj batch_id z poprzedniej sesji dla ponowienia
                batch_id = last_failed_log.batch_id
        
        # Data graniczna (14 dni temu)
        threshold_date = datetime.now() - timedelta(days=14)
        logger.info(f"Sprawdzam próbki wysłane po {threshold_date.date()}")
        
        # Pobranie wysłanych próbek z ostatnich 14 dni
        sent_samples = sample_repo.get_samples_by_status('Sent')
        recent_samples = [
            s for s in sent_samples 
            if s.date_sent >= threshold_date and s.date_sent <= datetime.now()
        ]
        
        logger.info(f"Znaleziono {len(recent_samples)} próbek wysłanych w ostatnich 14 dniach")
        
        # Sprawdź czy są próbki do przetworzenia
        if not recent_samples:
            logger.info("Brak próbek do przetworzenia. Zakończono.")
            return
        
        # Pobranie wszystkich notatek (do sprawdzania potwierdzeń)
        all_notes = note_repo.get_all_notes()
        if all_notes is None:
            logger.warning("Nie udało się pobrać notatek, używam pustej listy")
            all_notes = []
        
        # Słownik do grupowania zadań po sprzedawcy
        tasks_by_salesperson: Dict[str, List[TaskModel]] = defaultdict(list)
        
        # Przetwarzanie każdej próbki
        for sample in recent_samples:
            # Walidacja próbki
            if not sample:
                logger.warning("Napotkano pustą próbkę w liście, pomijam")
                continue
            
            if not sample.customer_id:
                logger.warning(f"Próbka ID {sample.id if hasattr(sample, 'id') else 'unknown'} nie ma customer_id, pomijam")
                continue
            
            if not sample.date_sent:
                logger.warning(f"Próbka ID {sample.id if hasattr(sample, 'id') else 'unknown'} nie ma date_sent, pomijam")
                continue
            logger.debug(f"Sprawdzam próbkę ID: {sample.id}, Klient: {sample.customer_id}, Data: {sample.date_sent.date()}")
            
            # 1. Sprawdź czy istnieje zadanie dla tej próbki
            existing_tasks = task_repo.get_tasks_by_customer_and_sample(
                sample.customer_id, 
                sample.id
            )
            
            if existing_tasks:
                logger.debug(f"Zadanie już istnieje dla próbki {sample.id}")
                continue
            
            # 2. Analizuj notatki używając LLM (Gemini, OpenAI lub Qwen)
            # Możesz zmienić dostawcę przekazując parametr: llm_provider="openai" lub "qwen"
            analysis_result = analyze_notes_with_llm(
                all_notes,
                sample.customer_id,
                sample.date_sent,
                llm_provider=None  # None = używa Config.LLM_PROVIDER
            )
            
            # Jeśli próbka dotarła (potwierdzenie otrzymania), pomijamy
            if analysis_result['sample_received']:
                best_analysis = analysis_result.get('best_note_analysis')
                status = best_analysis.get('sample_status') if best_analysis else 'unknown'
                logger.info(
                    f"LLM potwierdził otrzymanie próbki {sample.id} przez klienta {sample.customer_id}. "
                    f"Status: {status}, "
                    f"Zadowolenie: {analysis_result['customer_satisfied']}"
                )
                continue
            
            # Jeśli jest opóźnienie, również tworzymy zadanie (ale z innym opisem)
            if analysis_result['has_delay']:
                logger.info(
                    f"Gemini wykrył opóźnienie w dostawie próbki {sample.id} dla klienta {sample.customer_id}"
                )
                # Kontynuujemy do utworzenia zadania, ale z informacją o opóźnieniu
            
            # 3. Pobierz dane klienta (dla emaila sprzedawcy)
            customer = customer_repo.get_customer_by_id(sample.customer_id)
            if not customer:
                logger.warning(f"Nie znaleziono klienta {sample.customer_id} dla próbki {sample.id}")
                continue
            
            if not customer.salesperson_email:
                logger.warning(f"Klient {sample.customer_id} nie ma przypisanego sprzedawcy")
                continue
            
            # 4. Utwórz zadanie z informacjami z analizy LLM
            # Przygotuj opis zadania na podstawie analizy
            customer_name = customer.name if customer and customer.name else sample.customer_id
            
            if analysis_result['has_delay']:
                description = (
                    f"OPÓŹNIENIE: Klient {customer_name} ({sample.customer_id}) nie otrzymał jeszcze próbki "
                    f"wysłanej {sample.date_sent.date()}. Próbka ID: {sample.id}. "
                    f"Sprawdź status dostawy i skontaktuj się z klientem."
                )
                task_type = "SAMPLE_DELAY"
            elif analysis_result['has_confirmation'] and not analysis_result['sample_received']:
                # Jest mowa o próbce, ale nie ma potwierdzenia otrzymania
                description = (
                    f"Klient {customer_name} ({sample.customer_id}) wspomniał o próbce, "
                    f"ale brak potwierdzenia otrzymania. Próbka wysłana {sample.date_sent.date()}. "
                    f"Próbka ID: {sample.id}. Zweryfikuj status."
                )
                task_type = "SAMPLE_VERIFICATION"
            else:
                # Brak informacji o próbce w notatkach
                description = (
                    f"Sprawdź czy klient {customer_name} ({sample.customer_id}) otrzymał próbkę "
                    f"wysłaną {sample.date_sent.date()}. Próbka ID: {sample.id}. "
                    f"Brak informacji w notatkach."
                )
                task_type = "SAMPLE_FOLLOWUP"
            
            # Dodaj informacje o zadowoleniu klienta jeśli dostępne
            if analysis_result['customer_satisfied'] is not None:
                satisfaction_text = "zadowolony" if analysis_result['customer_satisfied'] else "niezadowolony"
                description += f" Klient jest {satisfaction_text}."
            
            task = TaskModel(
                id=None,  # Zostanie przypisane automatycznie
                customer_id=sample.customer_id,
                sample_id=sample.id,
                task_type=task_type,
                description=description,
                status="PENDING",
                assigned_to=customer.salesperson_email
            )
            
            created_task = task_repo.create_task(task)
            tasks_by_salesperson[customer.salesperson_email].append(created_task)
            
            logger.info(
                f"Utworzono zadanie ID: {created_task.id} dla sprzedawcy {customer.salesperson_email}, "
                f"klient: {customer.name}, próbka: {sample.id}"
            )
        
        # 5. Wysyłanie emaili do sprzedawców (jeden email z wszystkimi zadaniami)
        for salesperson_email, tasks in tasks_by_salesperson.items():
            if not tasks:
                continue
            
            logger.info(f"Przygotowuję email dla sprzedawcy {salesperson_email} ({len(tasks)} zadań)")
            
            # Sprawdź czy ten email był już w poprzedniej nieudanej próbie
            existing_log = None
            if salesperson_email in retry_emails:
                existing_log = retry_emails[salesperson_email]
                logger.info(f"Ponawiam wysyłkę do {salesperson_email} (log ID: {existing_log.id})")
            
            # Przygotowanie danych dla szablonu email
            tasks_data = []
            task_ids_list = []
            for task in tasks:
                if not task:
                    logger.warning("Napotkano puste zadanie w liście, pomijam")
                    continue
                
                customer = customer_repo.get_customer_by_id(task.customer_id) if task.customer_id else None
                sample = next((s for s in recent_samples if s.id == task.sample_id), None) if recent_samples else None
                
                tasks_data.append({
                    'task_id': task.id if task.id else 0,
                    'customer_name': customer.name if customer else task.customer_id or 'Nieznany',
                    'customer_id': task.customer_id or '',
                    'sample_id': task.sample_id if task.sample_id else 0,
                    'sample_date': sample.date_sent.date() if sample and sample.date_sent else 'N/A',
                    'description': task.description or 'Brak opisu'
                })
                task_ids_list.append(str(task.id) if task.id else '0')
            
            # Wysyłanie emaila
            context = {
                'salesperson_email': salesperson_email,
                'tasks': tasks_data,
                'tasks_count': len(tasks_data)
            }
            
            subject = f"Nowe zadania do wykonania - {len(tasks_data)} próbek wymaga weryfikacji"
            
            # Użyj batch_id z istniejącego logu lub nowego
            current_batch_id = existing_log.batch_id if existing_log else batch_id
            task_ids_str = ",".join(task_ids_list)
            
            success, log_id = mailer.send_notification(
                to_email=salesperson_email,
                subject=subject,
                template_name="email/tasks_notification.html",
                context=context,
                batch_id=current_batch_id,
                task_ids=task_ids_str,
                log_id=existing_log.id if existing_log else None
            )
            
            if success:
                logger.info(f"Email wysłany pomyślnie do {salesperson_email} (log ID: {log_id})")
            else:
                logger.error(f"Błąd wysyłania emaila do {salesperson_email} (log ID: {log_id})")
        
        total_tasks = sum(len(tasks) for tasks in tasks_by_salesperson.values())
        logger.info(f">>> Zakończono. Utworzono {total_tasks} zadań dla {len(tasks_by_salesperson)} sprzedawców")
        
    except Exception as e:
        logger.error(f"Błąd podczas monitorowania próbek: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

