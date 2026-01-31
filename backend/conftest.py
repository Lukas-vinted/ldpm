"""
Pytest configuration and fixtures for LDPM backend tests.
"""
import pytest


@pytest.fixture
def sample_display_data():
    """Sample display data for testing."""
    return {
        "name": "Test TV",
        "ip_address": "192.168.1.100",
        "psk": "test_psk_123",
        "location": "Conference Room",
        "tags": ["important", "test"]
    }


@pytest.fixture
def sample_group_data():
    """Sample group data for testing."""
    return {
        "name": "Test Group",
        "description": "A test group for unit testing"
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    return {
        "name": "Daily Startup",
        "action": "on",
        "cron_expression": "0 8 * * MON-FRI",
        "enabled": True
    }
