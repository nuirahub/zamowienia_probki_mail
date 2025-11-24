"""
Moduł do wysyłania emaili z użyciem szablonów Jinja2.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
from company_lib.config import Config
from company_lib.domain.interfaces import IMailLogRepository
from company_lib.domain.models import MailLogModel
from company_lib.logger import setup_logger

logger = setup_logger("Mailer")

class Mailer:
    """
    Klasa do wysyłania emaili z użyciem szablonów HTML.
    Obsługuje logowanie do repozytorium.
    """
    
    def __init__(self, mail_log_repo: Optional[IMailLogRepository] = None):
        """
        Inicjalizuje mailer z konfiguracją z Config.
        
        Args:
            mail_log_repo: Opcjonalne repozytorium do logowania wysyłek
        """
        self.server = Config.MAIL_SERVER
        self.port = Config.MAIL_PORT
        self.user = Config.MAIL_USER
        self.password = Config.MAIL_PASSWORD
        self.use_tls = Config.MAIL_USE_TLS
        self.mail_log_repo = mail_log_repo
        
        # Konfiguracja Jinja2 do ładowania szablonów
        template_dir = Config.TEMPLATE_DIR
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
        else:
            logger.warning(f"Katalog szablonów nie istnieje: {template_dir}")
            self.jinja_env = None
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderuje szablon HTML z kontekstem.
        
        Args:
            template_name: Nazwa pliku szablonu (np. 'email/notification.html')
            context: Słownik z danymi do wstawienia w szablon
        
        Returns:
            Zrenderowany HTML jako string
        """
        if not self.jinja_env:
            raise ValueError("Środowisko Jinja2 nie zostało zainicjalizowane")
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Błąd renderowania szablonu {template_name}: {e}")
            raise
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        batch_id: Optional[str] = None,
        task_ids: Optional[str] = None,
        log_id: Optional[int] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Wysyła email i loguje akcję.
        
        Args:
            to_email: Adres odbiorcy
            subject: Temat wiadomości
            body_html: Treść HTML
            body_text: Treść tekstowa (opcjonalna)
            from_email: Adres nadawcy (domyślnie z Config)
            batch_id: ID partii wysyłki (opcjonalne)
            task_ids: Lista ID zadań oddzielona przecinkami (opcjonalne)
            log_id: ID istniejącego logu (dla ponownej próby)
        
        Returns:
            Tuple (success: bool, log_id: Optional[int])
        """
        if not from_email:
            from_email = self.user
        
        # Utwórz log przed wysyłką (jeśli nie ma istniejącego)
        mail_log = None
        if self.mail_log_repo:
            if log_id:
                # Aktualizujemy istniejący log
                mail_log = next((l for l in self.mail_log_repo.logs if l.id == log_id), None)
                if mail_log:
                    mail_log.status = "PENDING"  # Reset statusu dla ponownej próby
            else:
                # Tworzymy nowy log
                mail_log = MailLogModel(
                    id=None,
                    to_email=to_email,
                    subject=subject,
                    status="PENDING",
                    batch_id=batch_id,
                    task_ids=task_ids
                )
                mail_log = self.mail_log_repo.create_log(mail_log)
        
        try:
            # Tworzenie wiadomości
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Dodanie treści tekstowej (jeśli podana)
            if body_text:
                part_text = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part_text)
            
            # Dodanie treści HTML
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Wysyłka
            with smtplib.SMTP(self.server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            # Aktualizuj log na SENT
            if self.mail_log_repo and mail_log:
                self.mail_log_repo.update_log_status(mail_log.id, "SENT")
            
            logger.info(f"Email wysłany pomyślnie do: {to_email}")
            return True, mail_log.id if mail_log else None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Błąd wysyłania emaila do {to_email}: {error_msg}")
            
            # Aktualizuj log na FAILED
            if self.mail_log_repo and mail_log:
                self.mail_log_repo.update_log_status(mail_log.id, "FAILED", error_msg)
            
            return False, mail_log.id if mail_log else None
    
    def send_notification(
        self,
        to_email: str,
        subject: str,
        template_name: str = "email/notification.html",
        context: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None,
        task_ids: Optional[str] = None,
        log_id: Optional[int] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Wysyła email używając szablonu.
        
        Args:
            to_email: Adres odbiorcy
            subject: Temat wiadomości
            template_name: Nazwa szablonu
            context: Kontekst dla szablonu
            batch_id: ID partii wysyłki (opcjonalne)
            task_ids: Lista ID zadań oddzielona przecinkami (opcjonalne)
            log_id: ID istniejącego logu (dla ponownej próby)
        
        Returns:
            Tuple (success: bool, log_id: Optional[int])
        """
        if context is None:
            context = {}
        
        try:
            body_html = self.render_template(template_name, context)
            return self.send_email(
                to_email, subject, body_html,
                batch_id=batch_id, task_ids=task_ids, log_id=log_id
            )
        except Exception as e:
            logger.error(f"Błąd wysyłania powiadomienia: {e}")
            return False, None

