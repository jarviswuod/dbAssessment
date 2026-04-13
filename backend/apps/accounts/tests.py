from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Role

User = get_user_model()


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        Role.objects.get_or_create(name=Role.ADMIN)
        Role.objects.get_or_create(name=Role.USER)

    def test_register_user(self):
        response = self.client.post("/api/v1/auth/register/", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["role"]["name"], "user")
        self.assertNotIn("password", response.data)

    def test_register_admin(self):
        # Only existing admins can create admin accounts
        admin_role = Role.objects.get(name=Role.ADMIN)
        admin = User.objects.create_user(
            username="existingadmin", password="securepass123", role=admin_role
        )
        self.client.force_authenticate(user=admin)
        response = self.client.post("/api/v1/auth/register/", {
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "securepass123",
            "role_name": "admin",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"]["name"], "admin")

    def test_register_admin_rejected_for_anonymous(self):
        response = self.client.post("/api/v1/auth/register/", {
            "username": "sneakyadmin",
            "email": "sneaky@example.com",
            "password": "securepass123",
            "role_name": "admin",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_rejected(self):
        response = self.client.post("/api/v1/auth/register/", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "role_name": "user",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_tokens(self):
        user_role = Role.objects.get(name=Role.USER)
        User.objects.create_user(
            username="logintest", password="securepass123", role=user_role
        )
        response = self.client.post("/api/v1/auth/login/", {
            "username": "logintest",
            "password": "securepass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username="logintest", password="securepass123")
        response = self.client.post("/api/v1/auth/login/", {
            "username": "logintest",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_auth(self):
        response = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_user_data(self):
        user_role = Role.objects.get(name=Role.USER)
        user = User.objects.create_user(
            username="profiletest", password="securepass123", role=user_role
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "profiletest")
