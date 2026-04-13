from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role
from apps.connections.models import ConnectionConfig
from apps.storage.models import SubmitJob, ProcessedDataRecord, ExportedFile

User = get_user_model()


class RBACTestCase(TestCase):
    """Test that RBAC is enforced at the API level, not just frontend."""

    def setUp(self):
        self.client = APIClient()
        admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        user_role, _ = Role.objects.get_or_create(name=Role.USER)

        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", role=admin_role
        )
        self.user1 = User.objects.create_user(
            username="user1", password="userpass123", role=user_role
        )
        self.user2 = User.objects.create_user(
            username="user2", password="userpass123", role=user_role
        )

        # user1's connection
        self.conn1 = ConnectionConfig.objects.create(
            owner=self.user1,
            name="User1 Postgres",
            db_type="postgres",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="testdb",
        )

    def test_user_sees_only_own_connections(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get("/api/v1/connections/")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 0)

    def test_admin_sees_all_connections(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/connections/")
        results = response.data.get("results", response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_user_cannot_access_others_connection(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f"/api/v1/connections/{self.conn1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_access_any_connection(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/connections/{self.conn1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_not_in_response(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/v1/connections/{self.conn1.id}/")
        self.assertNotIn("password", response.data)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SubmitDataTest(TestCase):
    """Test the async submit data flow."""

    def setUp(self):
        self.client = APIClient()
        admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        user_role, _ = Role.objects.get_or_create(name=Role.USER)

        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", role=admin_role
        )
        self.user1 = User.objects.create_user(
            username="user1", password="userpass123", role=user_role
        )
        self.user2 = User.objects.create_user(
            username="user2", password="userpass123", role=user_role
        )
        self.conn = ConnectionConfig.objects.create(
            owner=self.user1,
            name="Test Conn",
            db_type="postgres",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="testdb",
        )

    @patch("apps.storage.views.process_submit_job")
    def test_submit_returns_202_with_job(self, mock_task):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1, "name": "Alice"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["row_count"], 1)
        # Verify task was dispatched
        mock_task.delay.assert_called_once_with(response.data["id"])

    @patch("apps.storage.views.process_submit_job")
    def test_submit_creates_record_and_job(self, mock_task):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1, "name": "Alice"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        job = SubmitJob.objects.get(id=response.data["id"])
        self.assertEqual(job.user, self.user1)
        self.assertEqual(job.status, "pending")
        self.assertIsNotNone(job.record)
        self.assertEqual(job.record.row_count, 1)

    @patch("apps.storage.views.process_submit_job")
    def test_non_owner_cannot_submit(self, mock_task):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1, "name": "Alice"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_task.delay.assert_not_called()

    @patch("apps.storage.views.process_submit_job")
    def test_admin_can_submit_to_any_connection(self, mock_task):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1, "name": "Alice"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_submit_nonexistent_connection(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": 99999,
            "table_name": "employees",
            "data": [{"id": 1}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.storage.views.process_submit_job")
    def test_job_status_endpoint(self, mock_task):
        self.client.force_authenticate(user=self.user1)
        # Create a job via submit
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1}],
            "export_format": "json",
        }, format="json")
        job_id = response.data["id"]

        # Poll status
        status_resp = self.client.get(f"/api/v1/storage/jobs/{job_id}/")
        self.assertEqual(status_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(status_resp.data["id"], job_id)
        self.assertEqual(status_resp.data["status"], "pending")

    @patch("apps.storage.views.process_submit_job")
    def test_other_user_cannot_poll_job(self, mock_task):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"id": 1}],
            "export_format": "json",
        }, format="json")
        job_id = response.data["id"]

        # user2 tries to poll user1's job
        self.client.force_authenticate(user=self.user2)
        status_resp = self.client.get(f"/api/v1/storage/jobs/{job_id}/")
        self.assertEqual(status_resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.connections.connectors.factory.ConnectorFactory.from_config")
    def test_task_processes_job_to_completion(self, mock_from_config):
        from apps.storage.tasks import process_submit_job

        mock_connector = MagicMock()
        mock_connector.update_rows.return_value = 1
        mock_connector.__enter__ = MagicMock(return_value=mock_connector)
        mock_connector.__exit__ = MagicMock(return_value=False)
        mock_from_config.return_value = mock_connector

        record = ProcessedDataRecord.objects.create(
            user=self.user1,
            source_connection=self.conn,
            source_db_type="postgres",
            source_table="employees",
            data=[{"id": 1, "name": "Alice"}],
            row_count=1,
        )
        job = SubmitJob.objects.create(
            user=self.user1,
            connection=self.conn,
            table_name="employees",
            export_format="json",
            row_count=1,
            record=record,
        )

        process_submit_job(job.id)

        job.refresh_from_db()
        self.assertEqual(job.status, "completed")
        self.assertIsNotNone(job.exported_file)
        self.assertEqual(job.rows_updated_in_source, 1)
        self.assertIsNotNone(job.completed_at)


class FileDownloadShareTest(TestCase):
    """Test file download RBAC and share toggle."""

    def setUp(self):
        self.client = APIClient()
        admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        user_role, _ = Role.objects.get_or_create(name=Role.USER)

        self.admin = User.objects.create_user(
            username="admin", password="adminpass123", role=admin_role
        )
        self.user1 = User.objects.create_user(
            username="user1", password="userpass123", role=user_role
        )
        self.user2 = User.objects.create_user(
            username="user2", password="userpass123", role=user_role
        )
        self.conn = ConnectionConfig.objects.create(
            owner=self.user1,
            name="Test",
            db_type="postgres",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            database="testdb",
        )
        self.record = ProcessedDataRecord.objects.create(
            user=self.user1,
            source_connection=self.conn,
            source_db_type="postgres",
            source_table="employees",
            data=[{"id": 1}],
            row_count=1,
        )
        # Create a real file on disk for download tests
        import os
        from django.conf import settings
        os.makedirs(settings.EXPORTS_DIR, exist_ok=True)
        self.file_path = os.path.join(str(settings.EXPORTS_DIR), "test_download.json")
        with open(self.file_path, "w") as f:
            f.write('{"data": []}')

        self.exported_file = ExportedFile.objects.create(
            user=self.user1,
            processed_record=self.record,
            file_format="json",
            file_path=self.file_path,
            file_name="test_download.json",
            source_db_type="postgres",
            source_table="employees",
            is_shared=False,
        )

    def tearDown(self):
        import os
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_owner_can_download(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/v1/storage/files/{self.exported_file.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_download_unshared(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f"/api/v1/storage/files/{self.exported_file.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_admin_can_download_any_file(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/storage/files/{self.exported_file.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_toggle(self):
        self.client.force_authenticate(user=self.user1)
        # Toggle on
        response = self.client.post(f"/api/v1/storage/files/{self.exported_file.id}/share/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_shared"])
        # Toggle off
        response = self.client.post(f"/api/v1/storage/files/{self.exported_file.id}/share/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_shared"])

    def test_other_user_cannot_share(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"/api/v1/storage/files/{self.exported_file.id}/share/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_shared_file_downloadable_by_others(self):
        # Share the file first
        self.exported_file.is_shared = True
        self.exported_file.save()

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f"/api/v1/storage/files/{self.exported_file.id}/download/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_sees_own_and_shared_files(self):
        # user1's file is not shared — user2 shouldn't see it
        self.client.force_authenticate(user=self.user2)
        response = self.client.get("/api/v1/storage/files/")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 0)

        # Share it — now user2 should see it
        self.exported_file.is_shared = True
        self.exported_file.save()
        response = self.client.get("/api/v1/storage/files/")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_admin_sees_all_files(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/storage/files/")
        results = response.data.get("results", response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_unauthenticated_request_rejected(self):
        response = self.client.get("/api/v1/connections/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubmitDataRBACTest(TestCase):
    """Test RBAC enforcement on data submission."""

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

    def test_non_owner_cannot_submit_to_connection(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"name": "test"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.storage.views.process_submit_job")
    def test_owner_can_submit_to_own_connection(self, mock_task):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/storage/submit/", {
            "connection_id": self.conn.id,
            "table_name": "employees",
            "data": [{"name": "test"}],
            "export_format": "json",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
