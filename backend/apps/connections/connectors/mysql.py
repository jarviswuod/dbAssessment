import MySQLdb
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
        try:
            cur.execute("SHOW TABLES")
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()

    def get_columns(self, table: str) -> list[str]:
        table = self.validate_table_name(table)
        cur = self._connection.cursor()
        try:
            cur.execute(f"SHOW COLUMNS FROM `{table}`")
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        table = self.validate_table_name(table)
        cur = self._connection.cursor()
        try:
            cur.execute(f"SELECT * FROM `{table}` LIMIT %s OFFSET %s", (limit, offset))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            cur.close()

    def get_row_count(self, table: str) -> int:
        table = self.validate_table_name(table)
        cur = self._connection.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            return cur.fetchone()[0]
        finally:
            cur.close()

    def _get_primary_key(self, table: str) -> list[str]:
        cur = self._connection.cursor()
        try:
            cur.execute(f"SHOW KEYS FROM `{table}` WHERE Key_name = 'PRIMARY'")
            return [row[4] for row in cur.fetchall()]
        finally:
            cur.close()

    def update_rows(self, table: str, data: list[dict], original_data: list[dict] = None) -> int:
        pk_cols = self._get_primary_key(table)
        if not pk_cols or not data:
            return 0
        use_original = original_data and len(original_data) == len(data)
        updated = 0
        cur = self._connection.cursor()
        try:
            for i, row in enumerate(data):
                orig = original_data[i] if use_original else row
                non_pk = {k: v for k, v in row.items() if k not in pk_cols}
                if not non_pk:
                    continue
                set_clause = ", ".join(f"`{k}` = %s" for k in non_pk)
                where_clause = " AND ".join(f"`{k}` = %s" for k in pk_cols)
                values = list(non_pk.values()) + [orig[k] for k in pk_cols]
                cur.execute(
                    f"UPDATE `{table}` SET {set_clause} WHERE {where_clause}",
                    values,
                )
                updated += cur.rowcount
            self._connection.commit()
            return updated
        finally:
            cur.close()
