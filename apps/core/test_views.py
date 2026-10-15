"""Tests for core views."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIRequestFactory

from apps.core.views import health_live, health_ready


@pytest.mark.django_db
class TestHealthViews:
    """Test health check views."""

    def test_health_live(self):
        """Test liveness probe."""
        factory = APIRequestFactory()
        request = factory.get("/health/live")
        response = health_live(request)
        assert response.status_code == 200
        assert response.data["status"] == "alive"

    def test_health_ready_success(self):
        """Test readiness probe with healthy database."""
        factory = APIRequestFactory()
        request = factory.get("/health/ready")
        response = health_ready(request)
        assert response.status_code == 200
        assert response.data["status"] == "ready"

    @patch("apps.core.views.connections")
    def test_health_ready_failure(self, mock_connections):
        """Test readiness probe with database failure."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")
        mock_connections.__getitem__.return_value = mock_conn

        factory = APIRequestFactory()
        request = factory.get("/health/ready")
        response = health_ready(request)
        assert response.status_code == 503
        assert response.data["status"] == "not ready"
