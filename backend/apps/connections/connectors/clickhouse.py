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
        table = self.validate_table_name(table)
        result = self._connection.query(f"DESCRIBE TABLE `{table}`")
        return [row[0] for row in result.result_rows]

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        table = self.validate_table_name(table)
        result = self._connection.query(
            f"SELECT * FROM `{table}` LIMIT %(limit)s OFFSET %(offset)s",
            parameters={"limit": limit, "offset": offset},
        )
        columns = result.column_names
        return [dict(zip(columns, row)) for row in result.result_rows]

    def get_row_count(self, table: str) -> int:
        table = self.validate_table_name(table)
        result = self._connection.query(f"SELECT COUNT(*) FROM `{table}`")
        return result.result_rows[0][0]

    def _get_primary_key(self, table: str) -> list[str]:
        result = self._connection.query(
            "SELECT name FROM system.columns "
            "WHERE database = %(db)s AND table = %(tbl)s AND is_in_primary_key = 1",
            parameters={"db": self.database, "tbl": table},
        )
        return [row[0] for row in result.result_rows]

    @staticmethod
    def _ch_literal(v) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        return str(v)

    def update_rows(self, table: str, data: list[dict], original_data: list[dict] = None) -> int:
        if not data:
            return 0
        # Build pairs of (original_row, new_row) to detect per-row changes
        if original_data and len(original_data) == len(data):
            pairs = list(zip(original_data, data))
        else:
            return 0  # Cannot safely update without original data for ClickHouse

        updated = 0
        for orig_row, new_row in pairs:
            # Find which columns actually changed
            changed = {k: new_row[k] for k in new_row if str(new_row.get(k)) != str(orig_row.get(k))}
            if not changed:
                continue

            # WHERE uses ALL original columns to uniquely identify the row
            where_parts = [f"`{k}` = {self._ch_literal(v)}" for k, v in orig_row.items()]
            set_parts = [f"`{k}` = {self._ch_literal(v)}" for k, v in changed.items()]

            self._connection.command(
                f"ALTER TABLE `{table}` UPDATE {', '.join(set_parts)} "
                f"WHERE {' AND '.join(where_parts)} "
                f"SETTINGS mutations_sync = 1"
            )
            updated += 1
        return updated
