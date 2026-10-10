"""Tests for core serializers."""

import pytest
from django.contrib.auth import get_user_model

from apps.core.serializers import CustomTokenObtainPairSerializer, RegisterSerializer

User = get_user_model()


@pytest.mark.django_db
class TestRegisterSerializer:
    """Test RegisterSerializer."""

    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self):
        """Test serializer with password mismatch."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "different",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_password_too_short(self):
        """Test serializer with password too short."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_invalid_email(self):
        """Test serializer with invalid email."""
        data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_missing_fields(self):
        """Test serializer with missing fields."""
        data = {"username": "testuser"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:
    """Test CustomTokenObtainPairSerializer."""

    def test_get_token_with_custom_claims(self):
        """Test that custom claims are added to token."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        serializer = CustomTokenObtainPairSerializer()
        token = serializer.get_token(user)
        assert token["email"] == "test@example.com"
        assert token["username"] == "testuser"
