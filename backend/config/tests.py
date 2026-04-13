from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role

User = get_user_model()


class ErrorEnvelopeTest(TestCase):
    """Verify every error response uses the uniform {success, error: {code, message}} envelope."""

    def setUp(self):
        self.client = APIClient()
        Role.objects.get_or_create(name=Role.USER)
        Role.objects.get_or_create(name=Role.ADMIN)
        self.user = User.objects.create_user(
            username="envelopetest",
            password="pass12345678",
            role=Role.objects.get(name=Role.USER),
        )

    def _assert_error_envelope(self, response, expected_code):
        """Assert the response body matches the uniform error envelope."""
        self.assertFalse(response.data["success"])
        self.assertIn("error", response.data)
        self.assertIn("code", response.data["error"])
        self.assertIn("message", response.data["error"])
        self.assertEqual(response.data["error"]["code"], expected_code)
        self.assertIsInstance(response.data["error"]["message"], str)
        self.assertTrue(len(response.data["error"]["message"]) > 0)

    def test_401_not_authenticated(self):
        response = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._assert_error_envelope(response, "not_authenticated")

    def test_401_bad_credentials(self):
        User.objects.create_user(username="badlogin", password="pass12345678")
        response = self.client.post("/api/v1/auth/login/", {
            "username": "badlogin",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._assert_error_envelope(response, "authentication_failed")

    def test_400_validation_error(self):
        response = self.client.post("/api/v1/auth/register/", {
            "username": "",
            "password": "",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_error_envelope(response, "validation_error")
        # Validation errors should include field-level details
        self.assertIn("details", response.data["error"])

    def test_404_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/connections/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_error_envelope(response, "not_found")

    def test_404_extraction_connection_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/extraction/extract/", {
            "connection_id": 99999,
            "table_name": "employees",
            "batch_size": 10,
            "offset": 0,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_error_envelope(response, "not_found")

    def test_404_download_file_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/storage/files/99999/download/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_error_envelope(response, "not_found")

    def test_404_share_file_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/storage/files/99999/share/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_error_envelope(response, "not_found")

    def test_405_method_not_allowed(self):
        response = self.client.delete("/api/v1/auth/login/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self._assert_error_envelope(response, "method_not_allowed")

    def test_400_extraction_invalid_table_name(self):
        from apps.connections.models import ConnectionConfig
        conn = ConnectionConfig.objects.create(
            owner=self.user,
            name="Test",
            db_type="postgres",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="testdb",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/extraction/extract/", {
            "connection_id": conn.id,
            "table_name": "employees; DROP TABLE users; --",
            "batch_size": 10,
            "offset": 0,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_error_envelope(response, "validation_error")
