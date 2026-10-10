"""Serializers for authentication."""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional claims."""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token."""
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["username"] = user.username

        return token


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        """Validate that passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            error_msg = "Passwords do not match."
            raise serializers.ValidationError(error_msg)
        return attrs
