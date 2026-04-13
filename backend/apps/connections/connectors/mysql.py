try:
    import MySQLdb  # provided by mysqlclient
except ModuleNotFoundError:  # pragma: no cover
    import pymysql as MySQLdb

from .base import BaseConnector


class MySQLConnector(BaseConnector):
    def connect(self):
        self._connection = MySQLdb.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            passwd=self.password,
            db=self.database,
        )

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def list_tables(self) -> list[str]:
        cur = self._connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        return tables

    def get_columns(self, table: str) -> list[str]:
        cur = self._connection.cursor()
        cur.execute(f"SHOW COLUMNS FROM `{table}`")
        columns = [row[0] for row in cur.fetchall()]
        cur.close()
        return columns

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        cur = self._connection.cursor()
        cur.execute(f"SELECT * FROM `{table}` LIMIT %s OFFSET %s", (limit, offset))
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return rows

    def get_row_count(self, table: str) -> int:
        cur = self._connection.cursor()
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cur.fetchone()[0]
        cur.close()
        return count
