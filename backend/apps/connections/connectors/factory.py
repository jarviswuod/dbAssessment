from .base import BaseConnector
from .postgres import PostgresConnector
from .mongo import MongoConnector
from .clickhouse import ClickHouseConnector


class ConnectorFactory:
    """Factory to create the appropriate connector based on db_type."""

    _registry: dict[str, type[BaseConnector]] = {
        "postgres": PostgresConnector,
        "mongodb": MongoConnector,
        "clickhouse": ClickHouseConnector,
    }

    @classmethod
    def get(cls, db_type: str, **kwargs) -> BaseConnector:
        if db_type == "mysql" and "mysql" not in cls._registry:
            # Lazy import so the app can run without mysqlclient system deps.
            from .mysql import MySQLConnector  # noqa: WPS433

            cls._registry["mysql"] = MySQLConnector
        connector_cls = cls._registry.get(db_type)
        if not connector_cls:
            raise ValueError(f"Unsupported database type: {db_type}")
        return connector_cls(**kwargs)

    @classmethod
    def from_config(cls, config) -> BaseConnector:
        """Create a connector from a ConnectionConfig model instance."""
        return cls.get(
            db_type=config.db_type,
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            database=config.database,
        )
