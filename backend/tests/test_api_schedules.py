"""
TDD: Schedule API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import Schedule, Display, Group, Base
from app.db.database import engine, SessionLocal, get_db


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_display(db):
    display = Display(name="TV", ip_address="192.168.1.100", psk="psk", status="active")
    db.add(display)
    db.commit()
    db.refresh(display)
    return display


@pytest.fixture
def sample_schedule(db, sample_display):
    schedule = Schedule(
        name="Morning On",
        display_id=sample_display.id,
        action="on",
        cron_expression="0 7 * * MON-FRI",
        enabled=True
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


class TestScheduleList:
    def test_list_schedules_empty(self, client):
        response = client.get("/api/v1/schedules")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_schedules_single(self, client, sample_schedule):
        response = client.get("/api/v1/schedules")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestScheduleCreate:
    def test_create_schedule_success(self, client, sample_display):
        payload = {
            "name": "New Schedule",
            "display_id": sample_display.id,
            "action": "on",
            "cron_expression": "0 8 * * *",
            "enabled": True
        }
        response = client.post("/api/v1/schedules", json=payload)
        assert response.status_code == 201
        assert response.json()["name"] == "New Schedule"


class TestScheduleUpdate:
    def test_update_schedule_success(self, client, sample_schedule):
        payload = {"enabled": False}
        response = client.put(f"/api/v1/schedules/{sample_schedule.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["enabled"] is False


class TestScheduleDelete:
    def test_delete_schedule_success(self, client, sample_schedule):
        response = client.delete(f"/api/v1/schedules/{sample_schedule.id}")
        assert response.status_code == 204
