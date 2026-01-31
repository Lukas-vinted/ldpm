"""
TDD: Group API endpoint tests
Tests for Group CRUD operations and bulk power control endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.db.models import Group, Display, DisplayGroup, Base
from app.db.database import engine, SessionLocal, get_db


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_bravia_adapter():
    """Mock BraviaAdapter for power control tests."""
    adapter_instance = AsyncMock()
    yield adapter_instance


@pytest.fixture
def client(db, mock_bravia_adapter):
    """Create FastAPI test client with dependency overrides."""
    from app.api.groups import get_bravia_adapter
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
def sample_group(db):
    """Create a sample group in the database."""
    group = Group(name="Test Group", description="Test description")
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@pytest.fixture
def sample_displays(db):
    """Create sample displays in the database."""
    displays = [
        Display(name=f"TV {i}", ip_address=f"192.168.1.{i}", psk=f"psk_{i}", status="active")
        for i in range(1, 4)
    ]
    for display in displays:
        db.add(display)
    db.commit()
    for display in displays:
        db.refresh(display)
    return displays


class TestGroupList:
    """Tests for GET /api/v1/groups - List all groups."""
    
    def test_list_groups_empty(self, client):
        """Should return empty list when no groups exist."""
        response = client.get("/api/v1/groups")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_groups_single(self, client, sample_group):
        """Should return list with one group."""
        response = client.get("/api/v1/groups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_group.id
        assert data[0]["name"] == "Test Group"
        assert data[0]["display_count"] == 0


class TestGroupCreate:
    """Tests for POST /api/v1/groups - Create new group."""
    
    def test_create_group_success(self, client):
        """Should create group with valid data."""
        payload = {"name": "New Group", "description": "New description"}
        response = client.post("/api/v1/groups", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Group"
        assert data["description"] == "New description"
        assert "id" in data
    
    def test_create_group_duplicate_name(self, client, sample_group):
        """Should reject group with duplicate name."""
        payload = {"name": "Test Group", "description": "Duplicate"}
        response = client.post("/api/v1/groups", json=payload)
        assert response.status_code == 400


class TestGroupUpdate:
    """Tests for PUT /api/v1/groups/{id} - Update group."""
    
    def test_update_group_success(self, client, sample_group):
        """Should update group fields."""
        payload = {"name": "Updated Group"}
        response = client.put(f"/api/v1/groups/{sample_group.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Group"


class TestGroupDelete:
    """Tests for DELETE /api/v1/groups/{id} - Delete group."""
    
    def test_delete_group_success(self, client, sample_group):
        """Should delete group by ID."""
        response = client.delete(f"/api/v1/groups/{sample_group.id}")
        assert response.status_code == 204


class TestGroupDisplays:
    """Tests for managing group displays."""
    
    def test_add_displays_to_group(self, client, sample_group, sample_displays):
        """Should add displays to group."""
        display_ids = [d.id for d in sample_displays[:2]]
        payload = {"display_ids": display_ids}
        response = client.post(f"/api/v1/groups/{sample_group.id}/displays", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["display_count"] == 2
    
    def test_remove_displays_from_group(self, client, sample_group, sample_displays, db):
        """Should remove displays from group."""
        for display in sample_displays[:2]:
            db.add(DisplayGroup(group_id=sample_group.id, display_id=display.id))
        db.commit()
        
        display_ids = [sample_displays[0].id]
        response = client.request(
            "DELETE",
            f"/api/v1/groups/{sample_group.id}/displays",
            json={"display_ids": display_ids}
        )
        assert response.status_code == 200


class TestGroupBulkPower:
    """Tests for POST /api/v1/groups/{id}/power - Bulk power control."""
    
    def test_bulk_power_on_success(self, client, sample_group, sample_displays, db, mock_bravia_adapter):
        """Should power on all displays in group."""
        for display in sample_displays:
            db.add(DisplayGroup(group_id=sample_group.id, display_id=display.id))
        db.commit()
        
        mock_bravia_adapter.set_power.return_value = True
        
        payload = {"on": True}
        response = client.post(f"/api/v1/groups/{sample_group.id}/power", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_displays"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
    
    def test_bulk_power_partial_failure(self, client, sample_group, sample_displays, db, mock_bravia_adapter):
        """Should handle partial failures in bulk power control."""
        for display in sample_displays:
            db.add(DisplayGroup(group_id=sample_group.id, display_id=display.id))
        db.commit()
        
        mock_bravia_adapter.set_power.side_effect = [True, False, True]
        
        payload = {"on": False}
        response = client.post(f"/api/v1/groups/{sample_group.id}/power", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 2
        assert data["failed"] == 1
