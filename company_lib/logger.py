"""
Konfiguracja loggera z obsługą UTF-8 dla polskich znaków.
"""
import logging
import sys
from pathlib import Path
from company_lib.config import Config

def setup_logger(name: str = "AppLogger", log_file: Path = None) -> logging.Logger:
    """
    Konfiguruje i zwraca logger z obsługą UTF-8.
    
    Args:
        name: Nazwa loggera
        log_file: Ścieżka do pliku logów (domyślnie z Config)
    
    Returns:
        Skonfigurowany logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    
    # Zapobiegaj duplikowaniu handlerów
    if logger.handlers:
        return logger
    
    # Format logowania
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler plikowy - KLUCZOWE: encoding='utf-8'
    if log_file is None:
        log_file = Config.LOG_FILE
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler konsolowy (żebyś widział w VSC)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

