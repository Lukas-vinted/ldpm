"""
TDD: Display API endpoint tests
Tests for Display CRUD operations and power control endpoints.
Run these FIRST (should FAIL - RED phase), then implement routers to pass them (GREEN phase).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime
from app.main import app
from app.db.models import Display, Base
from app.db.database import engine, SessionLocal, get_db
from app.adapters.bravia import PowerStatus


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db, mock_bravia_adapter):
    """Create FastAPI test client with database and BraviaAdapter dependency overrides."""
    from app.api.displays import get_bravia_adapter
    from app.main import verify_credentials
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    def override_get_bravia():
        return mock_bravia_adapter
    
    def override_verify_credentials():
        return "test_user"
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_bravia_adapter] = override_get_bravia
    app.dependency_overrides[verify_credentials] = override_verify_credentials
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_display(db):
    """Create a sample display in the database."""
    display = Display(
        name="Test TV",
        ip_address="192.168.1.100",
        psk="test_psk_123",
        location="Conference Room",
        tags={"building": "A", "floor": 2},
        status="active"
    )
    db.add(display)
    db.commit()
    db.refresh(display)
    return display


@pytest.fixture
def mock_bravia_adapter():
    """Mock BraviaAdapter for power control tests."""
    adapter_instance = AsyncMock()
    yield adapter_instance


class TestDisplayList:
    """Tests for GET /api/v1/displays - List all displays."""
    
    def test_list_displays_empty(self, client):
        """Should return empty list when no displays exist."""
        response = client.get("/api/v1/displays")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_displays_single(self, client, sample_display):
        """Should return list with one display."""
        response = client.get("/api/v1/displays")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_display.id
        assert data[0]["name"] == "Test TV"
        assert data[0]["ip_address"] == "192.168.1.100"
        assert data[0]["status"] == "active"
    
    def test_list_displays_multiple(self, client, db):
        """Should return list with multiple displays."""
        displays = [
            Display(name=f"TV {i}", ip_address=f"192.168.1.{i}", psk=f"psk_{i}", status="active")
            for i in range(1, 4)
        ]
        for display in displays:
            db.add(display)
        db.commit()
        
        response = client.get("/api/v1/displays")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestDisplayCreate:
    """Tests for POST /api/v1/displays - Create new display."""
    
    def test_create_display_success(self, client):
        """Should create display with valid data."""
        payload = {
            "name": "New TV",
            "ip_address": "192.168.1.200",
            "psk": "new_psk_123",
            "location": "Lobby",
            "tags": {"type": "4k"}
        }
        response = client.post("/api/v1/displays", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New TV"
        assert data["ip_address"] == "192.168.1.200"
        assert data["psk"] == "new_psk_123"
        assert data["location"] == "Lobby"
        assert data["tags"] == {"type": "4k"}
        assert data["status"] == "unknown"  # Default status
        assert "id" in data
        assert "created_at" in data
    
    def test_create_display_minimal(self, client):
        """Should create display with only required fields."""
        payload = {
            "name": "Minimal TV",
            "ip_address": "192.168.1.201",
            "psk": "minimal_psk"
        }
        response = client.post("/api/v1/displays", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal TV"
        assert data["location"] is None
        assert data["tags"] == {}
    
    def test_create_display_duplicate_ip(self, client, sample_display):
        """Should reject display with duplicate IP address."""
        payload = {
            "name": "Duplicate TV",
            "ip_address": "192.168.1.100",  # Same as sample_display
            "psk": "duplicate_psk"
        }
        response = client.post("/api/v1/displays", json=payload)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_display_missing_required_fields(self, client):
        """Should reject display with missing required fields."""
        payload = {"name": "Incomplete TV"}  # Missing ip_address and psk
        response = client.post("/api/v1/displays", json=payload)
        assert response.status_code == 422


class TestDisplayGet:
    """Tests for GET /api/v1/displays/{id} - Get single display."""
    
    def test_get_display_success(self, client, sample_display):
        """Should return display by ID."""
        response = client.get(f"/api/v1/displays/{sample_display.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_display.id
        assert data["name"] == "Test TV"
        assert data["ip_address"] == "192.168.1.100"
    
    def test_get_display_not_found(self, client):
        """Should return 404 for non-existent display."""
        response = client.get("/api/v1/displays/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDisplayUpdate:
    """Tests for PUT /api/v1/displays/{id} - Update display."""
    
    def test_update_display_full(self, client, sample_display):
        """Should update all fields of a display."""
        payload = {
            "name": "Updated TV",
            "ip_address": "192.168.1.150",
            "psk": "updated_psk",
            "location": "New Location",
            "tags": {"updated": True},
            "status": "standby"
        }
        response = client.put(f"/api/v1/displays/{sample_display.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_display.id
        assert data["name"] == "Updated TV"
        assert data["ip_address"] == "192.168.1.150"
        assert data["psk"] == "updated_psk"
        assert data["location"] == "New Location"
        assert data["tags"] == {"updated": True}
        assert data["status"] == "standby"
    
    def test_update_display_partial(self, client, sample_display):
        """Should update only specified fields."""
        payload = {"name": "Partially Updated TV"}
        response = client.put(f"/api/v1/displays/{sample_display.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partially Updated TV"
        assert data["ip_address"] == "192.168.1.100"  # Unchanged
    
    def test_update_display_not_found(self, client):
        """Should return 404 for non-existent display."""
        payload = {"name": "Ghost TV"}
        response = client.put("/api/v1/displays/9999", json=payload)
        assert response.status_code == 404


class TestDisplayDelete:
    """Tests for DELETE /api/v1/displays/{id} - Delete display."""
    
    def test_delete_display_success(self, client, sample_display):
        """Should delete display by ID."""
        response = client.delete(f"/api/v1/displays/{sample_display.id}")
        assert response.status_code == 204
        
        # Verify display is deleted
        get_response = client.get(f"/api/v1/displays/{sample_display.id}")
        assert get_response.status_code == 404
    
    def test_delete_display_not_found(self, client):
        """Should return 404 for non-existent display."""
        response = client.delete("/api/v1/displays/9999")
        assert response.status_code == 404


class TestDisplayPower:
    """Tests for POST /api/v1/displays/{id}/power - Power control."""
    
    def test_power_on_success(self, client, sample_display, mock_bravia_adapter):
        """Should power on display successfully."""
        mock_bravia_adapter.set_power.return_value = True
        
        payload = {"on": True}
        response = client.post(f"/api/v1/displays/{sample_display.id}/power", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "powered on" in data["message"].lower()
        
        # Verify BraviaAdapter was called correctly
        mock_bravia_adapter.set_power.assert_called_once()
        call_args = mock_bravia_adapter.set_power.call_args
        assert call_args[0][0] == "192.168.1.100"  # IP
        assert call_args[0][1] == "test_psk_123"  # PSK
        assert call_args[0][2] is True  # on=True
    
    def test_power_off_success(self, client, sample_display, mock_bravia_adapter):
        """Should power off display successfully."""
        mock_bravia_adapter.set_power.return_value = True
        
        payload = {"on": False}
        response = client.post(f"/api/v1/displays/{sample_display.id}/power", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "powered off" in data["message"].lower()
    
    def test_power_control_failure(self, client, sample_display, mock_bravia_adapter):
        """Should handle power control failure."""
        mock_bravia_adapter.set_power.return_value = False
        
        payload = {"on": True}
        response = client.post(f"/api/v1/displays/{sample_display.id}/power", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "failed" in data["detail"].lower()
    
    def test_power_control_not_found(self, client, mock_bravia_adapter):
        """Should return 404 for non-existent display."""
        payload = {"on": True}
        response = client.post("/api/v1/displays/9999/power", json=payload)
        assert response.status_code == 404


class TestDisplayStatus:
    """Tests for GET /api/v1/displays/{id}/status - Get power status."""
    
    def test_get_status_active(self, client, sample_display, mock_bravia_adapter):
        """Should return active power status."""
        mock_bravia_adapter.get_power_status.return_value = "active"
        
        response = client.get(f"/api/v1/displays/{sample_display.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["display_id"] == sample_display.id
        assert data["status"] == "active"
        assert "last_checked" in data
        
        # Verify BraviaAdapter was called
        mock_bravia_adapter.get_power_status.assert_called_once_with(
            "192.168.1.100", "test_psk_123"
        )
    
    def test_get_status_standby(self, client, sample_display, mock_bravia_adapter):
        """Should return standby power status."""
        mock_bravia_adapter.get_power_status.return_value = "standby"
        
        response = client.get(f"/api/v1/displays/{sample_display.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "standby"
    
    def test_get_status_error(self, client, sample_display, mock_bravia_adapter):
        """Should return error status when communication fails."""
        mock_bravia_adapter.get_power_status.return_value = "error"
        
        response = client.get(f"/api/v1/displays/{sample_display.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
    
    def test_get_status_not_found(self, client, mock_bravia_adapter):
        """Should return 404 for non-existent display."""
        response = client.get("/api/v1/displays/9999/status")
        assert response.status_code == 404
