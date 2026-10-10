"""Tests for authentication API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class RegisterAPITests(TestCase):
    """Tests for POST /api/v1/auth/register/ endpoint."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = APIClient()

    def test_register_user_success(self) -> None:
        """Test registering a new user successfully."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123",
            "password_confirm": "TestPassword123",
        }

        response = self.client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == 201
        assert response.data["username"] == "testuser"
        assert User.objects.filter(username="testuser").exists()

    def test_register_with_mismatched_passwords_raises_error(self) -> None:
        """Test registering with mismatched passwords raises error."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123",
            "password_confirm": "DifferentPassword123",
        }

        response = self.client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == 400

    def test_register_with_short_password_raises_error(self) -> None:
        """Test registering with short password raises error."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Short",
            "password_confirm": "Short",
        }

        response = self.client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == 400

    def test_register_with_duplicate_username_raises_error(self) -> None:
        """Test registering with duplicate username raises error."""
        User.objects.create_user(
            username="testuser", email="existing@example.com", password="password123"
        )

        data = {
            "username": "testuser",
            "email": "new@example.com",
            "password": "TestPassword123",
            "password_confirm": "TestPassword123",
        }

        response = self.client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == 400


class LoginAPITests(TestCase):
    """Tests for POST /api/v1/auth/login/ endpoint."""

    def setUp(self) -> None:
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
        )

    def test_login_success(self) -> None:
        """Test logging in with valid credentials."""
        data = {
            "username": "testuser",
            "password": "TestPassword123",
        }

        response = self.client.post("/api/v1/auth/login/", data, format="json")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_with_invalid_password_raises_error(self) -> None:
        """Test logging in with invalid password raises error."""
        data = {
            "username": "testuser",
            "password": "WrongPassword123",
        }

        response = self.client.post("/api/v1/auth/login/", data, format="json")

        assert response.status_code == 401

    def test_login_with_nonexistent_user_raises_error(self) -> None:
        """Test logging in with non-existent user raises error."""
        data = {
            "username": "nonexistent",
            "password": "TestPassword123",
        }

        response = self.client.post("/api/v1/auth/login/", data, format="json")

        assert response.status_code == 401
