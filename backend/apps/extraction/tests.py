from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role
from apps.connections.models import ConnectionConfig

User = get_user_model()


class ExtractDataRBACTest(TestCase):
    """Test that extraction respects ownership."""

    def setUp(self):
        self.client = APIClient()
        user_role, _ = Role.objects.get_or_create(name=Role.USER)
        self.user1 = User.objects.create_user(
            username="user1", password="pass123", role=user_role
        )
        self.user2 = User.objects.create_user(
            username="user2", password="pass123", role=user_role
        )
        self.conn = ConnectionConfig.objects.create(
            owner=self.user1,
            name="User1 DB",
            db_type="postgres",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="testdb",
        )

    def test_non_owner_cannot_extract(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post("/api/v1/extraction/extract/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "batch_size": 10,
            "offset": 0,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.extraction.views.ConnectorFactory")
    def test_owner_can_extract(self, mock_factory):
        mock_connector = MagicMock()
        mock_connector.get_row_count.return_value = 2
        mock_connector.fetch_batch.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_connector.get_columns.return_value = ["id", "name"]
        mock_connector.__enter__ = MagicMock(return_value=mock_connector)
        mock_connector.__exit__ = MagicMock(return_value=False)
        mock_factory.from_config.return_value = mock_connector

        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/extraction/extract/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "batch_size": 10,
            "offset": 0,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["total_rows"], 2)

    def test_sql_injection_table_name_rejected(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/extraction/extract/", {
            "connection_id": self.conn.id,
            "table_name": "employees; DROP TABLE users; --",
            "batch_size": 10,
            "offset": 0,
        }, format="json")
        # Should fail at connector level (either 400 or 404, not 500)
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ])
