import clickhouse_connect
from .base import BaseConnector


class ClickHouseConnector(BaseConnector):
    def connect(self):
        self._connection = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
        )

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def list_tables(self) -> list[str]:
        result = self._connection.query("SHOW TABLES")
        return [row[0] for row in result.result_rows]

    def get_columns(self, table: str) -> list[str]:
        result = self._connection.query(f"DESCRIBE TABLE `{table}`")
        return [row[0] for row in result.result_rows]

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        result = self._connection.query(
            f"SELECT * FROM `{table}` LIMIT %(limit)s OFFSET %(offset)s",
            parameters={"limit": limit, "offset": offset},
        )
        columns = result.column_names
        return [dict(zip(columns, row)) for row in result.result_rows]

    def get_row_count(self, table: str) -> int:
        result = self._connection.query(f"SELECT COUNT(*) FROM `{table}`")
        return result.result_rows[0][0]
