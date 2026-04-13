import psycopg2
import psycopg2.extras
from .base import BaseConnector


class PostgresConnector(BaseConnector):
    def connect(self):
        self._connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            dbname=self.database,
        )

    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    def list_tables(self) -> list[str]:
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            return [row[0] for row in cur.fetchall()]

    def get_columns(self, table: str) -> list[str]:
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "ORDER BY ordinal_position",
                (table,),
            )
            return [row[0] for row in cur.fetchall()]

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        with self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'SELECT * FROM "{table}" LIMIT %s OFFSET %s',
                (limit, offset),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def get_row_count(self, table: str) -> int:
        with self._connection.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            return cur.fetchone()[0]
