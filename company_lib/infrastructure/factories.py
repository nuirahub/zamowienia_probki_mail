"""
Fabryka repozytoriów - decyduje czy użyć SQL czy CSV na podstawie konfiguracji.
"""
from pathlib import Path
from company_lib.config import Config
from company_lib.core.database import MSSQLConnection
from company_lib.domain.repositories import (
    CustomerRepository,
    NoteRepository,
    SampleRepository
)
from company_lib.infrastructure.repo_csv import (
    CsvCustomerRepository,
    CsvNoteRepository,
    CsvSampleRepository
)
from company_lib.logger import setup_logger

logger = setup_logger("RepositoryFactory")

def get_customer_repository(note_repo=None, sample_repo=None):
    """
    Tworzy repozytorium klientów (SQL lub CSV) na podstawie konfiguracji.
    
    Args:
        note_repo: Opcjonalne repozytorium notatek (dla statystyk w trybie CSV)
        sample_repo: Opcjonalne repozytorium próbek (dla statystyk w trybie CSV)
    
    Returns:
        ICustomerRepository - implementacja repozytorium klientów
    """
    if Config.USE_MOCK_DATA:
        if not Config.MOCK_DIR:
            raise ValueError("USE_MOCK_DATA=True, ale katalog data/mocks nie istnieje")
        csv_path = Config.MOCK_DIR / "customers.csv"
        logger.info(f"Używam CSV repozytorium: {csv_path}")
        return CsvCustomerRepository(csv_path, note_repo=note_repo, sample_repo=sample_repo)
    else:
        logger.info("Używam SQL repozytorium")
        db = MSSQLConnection(Config.DB_STRING)
        return CustomerRepository(db)

def get_note_repository():
    """
    Tworzy repozytorium notatek (SQL lub CSV) na podstawie konfiguracji.
    
    Returns:
        INoteRepository - implementacja repozytorium notatek
    """
    if Config.USE_MOCK_DATA:
        if not Config.MOCK_DIR:
            raise ValueError("USE_MOCK_DATA=True, ale katalog data/mocks nie istnieje")
        csv_path = Config.MOCK_DIR / "notes.csv"
        logger.info(f"Używam CSV repozytorium: {csv_path}")
        return CsvNoteRepository(csv_path)
    else:
        logger.info("Używam SQL repozytorium")
        db = MSSQLConnection(Config.DB_STRING)
        return NoteRepository(db)

def get_sample_repository():
    """
    Tworzy repozytorium próbek (SQL lub CSV) na podstawie konfiguracji.
    
    Returns:
        ISampleRepository - implementacja repozytorium próbek
    """
    if Config.USE_MOCK_DATA:
        if not Config.MOCK_DIR:
            raise ValueError("USE_MOCK_DATA=True, ale katalog data/mocks nie istnieje")
        csv_path = Config.MOCK_DIR / "samples.csv"
        logger.info(f"Używam CSV repozytorium: {csv_path}")
        return CsvSampleRepository(csv_path)
    else:
        logger.info("Używam SQL repozytorium")
        db = MSSQLConnection(Config.DB_STRING)
        return SampleRepository(db)

def get_all_repositories():
    """
    Tworzy wszystkie repozytoria jednocześnie.
    W trybie SQL używa tego samego połączenia do bazy.
    W trybie CSV, repozytoria są powiązane dla statystyk.
    
    Returns:
        Tuple (CustomerRepository, NoteRepository, SampleRepository)
    """
    if Config.USE_MOCK_DATA:
        if not Config.MOCK_DIR:
            raise ValueError("USE_MOCK_DATA=True, ale katalog data/mocks nie istnieje")
        logger.info("Używam CSV repozytoriów")
        # Tworzymy najpierw note i sample, potem customer z referencjami
        note_repo = CsvNoteRepository(Config.MOCK_DIR / "notes.csv")
        sample_repo = CsvSampleRepository(Config.MOCK_DIR / "samples.csv")
        customer_repo = CsvCustomerRepository(
            Config.MOCK_DIR / "customers.csv",
            note_repo=note_repo,
            sample_repo=sample_repo
        )
        return (customer_repo, note_repo, sample_repo)
    else:
        logger.info("Używam SQL repozytoriów")
        db = MSSQLConnection(Config.DB_STRING)
        return (
            CustomerRepository(db),
            NoteRepository(db),
            SampleRepository(db)
        )

