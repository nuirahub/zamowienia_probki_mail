"""
Połączenie z bazą danych MSSQL z obsługą context manager.
"""
import pyodbc
from typing import List, Tuple, Optional, Any
from company_lib.logger import setup_logger

logger = setup_logger("Database")

class MSSQLConnection:
    """
    Klasa do zarządzania połączeniem z bazą danych MSSQL.
    Wspiera context manager (with statement) dla automatycznego zamykania połączenia.
    """
    
    def __init__(self, connection_string: str):
        """
        Inicjalizuje połączenie z bazą danych.
        
        Args:
            connection_string: String połączenia do bazy MSSQL
        """
        self.connection_string = connection_string
        self.connection: Optional[pyodbc.Connection] = None
        self.cursor: Optional[pyodbc.Cursor] = None
    
    def __enter__(self):
        """Otwiera połączenie przy wejściu do context managera."""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            logger.debug("Połączenie z bazą danych otwarte")
            return self
        except Exception as e:
            logger.error(f"Błąd połączenia z bazą danych: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Zamyka połączenie przy wyjściu z context managera."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.debug("Połączenie z bazą danych zamknięte")
        return False  # Nie tłumimy wyjątków
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Tuple]:
        """
        Wykonuje zapytanie SELECT i zwraca wyniki.
        
        Args:
            query: Zapytanie SQL
            params: Parametry do zapytania (opcjonalne)
        
        Returns:
            Lista krotek z wynikami
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Błąd wykonania zapytania: {e}\nQuery: {query}")
            raise
    
    def execute_non_query(self, query: str, params: Tuple = None) -> int:
        """
        Wykonuje zapytanie INSERT/UPDATE/DELETE.
        
        Args:
            query: Zapytanie SQL
            params: Parametry do zapytania (opcjonalne)
        
        Returns:
            Liczba zmienionych wierszy
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Błąd wykonania zapytania: {e}\nQuery: {query}")
            raise
    
    def execute_scalar(self, query: str, params: Tuple = None) -> Any:
        """
        Wykonuje zapytanie i zwraca pojedynczą wartość.
        
        Args:
            query: Zapytanie SQL
            params: Parametry do zapytania (opcjonalne)
        
        Returns:
            Pojedyncza wartość z pierwszego wiersza i pierwszej kolumny
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Błąd wykonania zapytania: {e}\nQuery: {query}")
            raise

