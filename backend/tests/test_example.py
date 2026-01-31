"""
Example test to verify pytest setup is working correctly.
"""


def test_example_simple_assertion():
    """Simple test to verify pytest setup works."""
    result = 1 + 1
    assert result == 2


def test_example_with_fixture(sample_display_data):
    """Test using a fixture from conftest."""
    assert sample_display_data["name"] == "Test TV"
    assert sample_display_data["ip_address"] == "192.168.1.100"
    assert "important" in sample_display_data["tags"]
