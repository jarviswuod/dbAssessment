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
        collection = self._connection[table]
        sample = collection.find_one()
        if sample:
            return list(sample.keys())
        return []

    def fetch_batch(self, table: str, offset: int, limit: int) -> list[dict]:
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
        return self._connection[table].count_documents({})
