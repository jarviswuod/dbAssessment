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
        table = self.validate_table_name(table)
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "ORDER BY ordinal_position",
                (table,),
            )
            return [row[0] for row in cur.fetchall()]

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        table = self.validate_table_name(table)
        with self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'SELECT * FROM "{table}" LIMIT %s OFFSET %s',
                (limit, offset),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def get_row_count(self, table: str) -> int:
        table = self.validate_table_name(table)
        with self._connection.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            return cur.fetchone()[0]

    def _get_primary_key(self, table: str) -> list[str]:
        with self._connection.cursor() as cur:
            cur.execute(
                "SELECT a.attname FROM pg_index i "
                "JOIN pg_attribute a ON a.attrelid = i.indrelid "
                "AND a.attnum = ANY(i.indkey) "
                "WHERE i.indrelid = %s::regclass AND i.indisprimary",
                (table,),
            )
            return [row[0] for row in cur.fetchall()]

    def update_rows(self, table: str, data: list[dict], original_data: list[dict] = None) -> int:
        pk_cols = self._get_primary_key(table)
        if not pk_cols or not data:
            return 0
        # Use original_data for WHERE if provided, to handle non-unique scenarios
        use_original = original_data and len(original_data) == len(data)
        updated = 0
        with self._connection.cursor() as cur:
            for i, row in enumerate(data):
                orig = original_data[i] if use_original else row
                non_pk = {k: row[k] for k in row if k not in pk_cols}
                if not non_pk:
                    continue
                set_clause = ", ".join(f'"{k}" = %s' for k in non_pk)
                where_clause = " AND ".join(f'"{k}" = %s' for k in pk_cols)
                values = list(non_pk.values()) + [orig[k] for k in pk_cols]
                cur.execute(
                    f'UPDATE "{table}" SET {set_clause} WHERE {where_clause}',
                    values,
                )
                updated += cur.rowcount
        self._connection.commit()
        return updated
