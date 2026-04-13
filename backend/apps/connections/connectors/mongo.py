from pymongo import MongoClient
from bson import ObjectId
from .base import BaseConnector


class MongoConnector(BaseConnector):
    def connect(self):
        self._client = MongoClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            authSource="admin",
        )
        self._connection = self._client[self.database]

    def close(self):
        if hasattr(self, "_client") and self._client:
            self._client.close()
            self._client = None
            self._connection = None

    def list_tables(self) -> list[str]:
        return self._connection.list_collection_names()

    def get_columns(self, table: str) -> list[str]:
        table = self.validate_table_name(table)
        collection = self._connection[table]
        sample = collection.find_one()
        if sample:
            return list(sample.keys())
        return []

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
        table = self.validate_table_name(table)
        collection = self._connection[table]
        cursor = collection.find().skip(offset).limit(limit)
        rows = []
        for doc in cursor:
            serialized = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    serialized[key] = str(value)
                else:
                    serialized[key] = value
            rows.append(serialized)
        return rows

    def get_row_count(self, table: str) -> int:
        table = self.validate_table_name(table)
        return self._connection[table].count_documents({})

    def update_rows(self, table: str, data: list[dict], original_data: list[dict] = None) -> int:
        collection = self._connection[table]
        use_original = original_data and len(original_data) == len(data)
        updated = 0
        for i, doc in enumerate(data):
            orig = original_data[i] if use_original else doc
            doc_id = orig.get("_id")
            if doc_id is None:
                continue
            update_fields = {k: v for k, v in doc.items() if k != "_id"}
            if not update_fields:
                continue
            try:
                filter_id = ObjectId(doc_id) if isinstance(doc_id, str) and len(doc_id) == 24 else doc_id
            except Exception:
                filter_id = doc_id
            result = collection.update_one({"_id": filter_id}, {"$set": update_fields})
            updated += result.modified_count
        return updated
