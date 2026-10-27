"""Tests for dashboard authentication."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardAuthenticationTests(TestCase):
    """Tests for dashboard authentication."""

    def setUp(self) -> None:
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
        )

    def test_login_page_accessible(self) -> None:
        """Test that login page is accessible without authentication."""
        response = self.client.get(reverse("dashboard:login"))
        assert response.status_code == 200
        self.assertContains(response, "Entrar")

    def test_login_with_valid_credentials(self) -> None:
        """Test login with valid credentials."""
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "testuser", "password": "TestPassword123"},
        )
        assert response.status_code == 302
        self.assertRedirects(response, reverse("dashboard:overview"))

    def test_login_with_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "testuser", "password": "WrongPassword"},
        )
        assert response.status_code == 200

    def test_logout(self) -> None:
        """Test logout functionality."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.post(reverse("dashboard:logout"))
        assert response.status_code == 302
        self.assertRedirects(response, reverse("dashboard:login"))

    def test_protected_view_redirects_to_login(self) -> None:
        """Test that protected views redirect to login when not authenticated."""
        response = self.client.get(reverse("dashboard:overview"))
        assert response.status_code == 302
        self.assertRedirects(
            response, f"{reverse('dashboard:login')}?next={reverse('dashboard:overview')}"
        )

    def test_protected_view_accessible_when_authenticated(self) -> None:
        """Test that protected views are accessible when authenticated."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.get(reverse("dashboard:overview"))
        assert response.status_code == 200

    def test_orders_page_requires_authentication(self) -> None:
        """Test that orders page requires authentication."""
        response = self.client.get(reverse("dashboard:orders"))
        assert response.status_code == 302

    def test_dead_letters_page_requires_authentication(self) -> None:
        """Test that dead letters page requires authentication."""
        response = self.client.get(reverse("dashboard:dead_letters"))
        assert response.status_code == 302

    def test_laboratory_page_requires_authentication(self) -> None:
        """Test that laboratory page requires authentication."""
        response = self.client.get(reverse("dashboard:laboratory"))
        assert response.status_code == 302

    def test_health_page_requires_authentication(self) -> None:
        """Test that health page requires authentication."""
        response = self.client.get(reverse("dashboard:health"))
        assert response.status_code == 302

    def test_authenticated_user_can_access_orders(self) -> None:
        """Test that authenticated user can access orders page."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.get(reverse("dashboard:orders"))
        assert response.status_code == 200

    def test_authenticated_user_can_access_dead_letters(self) -> None:
        """Test that authenticated user can access dead letters page."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.get(reverse("dashboard:dead_letters"))
        assert response.status_code == 200

    def test_authenticated_user_can_access_laboratory(self) -> None:
        """Test that authenticated user can access laboratory page."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.get(reverse("dashboard:laboratory"))
        assert response.status_code == 200

    def test_authenticated_user_can_access_health(self) -> None:
        """Test that authenticated user can access health page."""
        self.client.login(username="testuser", password="TestPassword123")
        response = self.client.get(reverse("dashboard:health"))
        assert response.status_code == 200
