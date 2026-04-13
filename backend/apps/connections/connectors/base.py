from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base for all database connectors."""

    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self._connection = None

    @abstractmethod
    def connect(self):
        """Establish connection to the database."""

    @abstractmethod
    def close(self):
        """Close the database connection."""

    @abstractmethod
    def list_tables(self) -> list[str]:
        """Return a list of available table/collection names."""

    @abstractmethod
    def get_columns(self, table: str) -> list[str]:
        """Return column names for a given table."""

    @abstractmethod
    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict[str, Any]]:
        """Fetch a batch of rows from the specified table."""

    @abstractmethod
    def get_row_count(self, table: str) -> int:
        """Return total number of rows in a table."""

    def test_connection(self) -> bool:
        """Test if connection can be established."""
        try:
            self.connect()
            self.close()
            return True
        except Exception:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
