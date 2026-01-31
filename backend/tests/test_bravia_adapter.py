"""
Tests for Sony BRAVIA adapter modules.

This module provides comprehensive tests for:
- BraviaRestAdapter (REST API control)
- BraviaSimpleIPAdapter (Simple IP Control)
- BraviaAdapter (facade with fallback logic)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBraviaRestAdapter:
    """Tests for BraviaRestAdapter (REST API control)."""

    @pytest.mark.asyncio
    async def test_rest_get_power_status_active(self):
        """Test REST adapter returns 'active' status."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        # Mock httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"status": "active"}]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "active"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://192.168.1.100/sony/system"
            assert call_args[1]["headers"]["X-Auth-PSK"] == "test_psk"
            assert call_args[1]["json"]["method"] == "getPowerStatus"

    @pytest.mark.asyncio
    async def test_rest_get_power_status_standby(self):
        """Test REST adapter returns 'standby' status."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"status": "standby"}]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "standby"

    @pytest.mark.asyncio
    async def test_rest_set_power_on(self):
        """Test REST adapter sends power ON command."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [], "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            result = await adapter.set_power("192.168.1.100", "test_psk", True)

            assert result is True
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["method"] == "setPowerStatus"
            assert call_args[1]["json"]["params"] == [{"status": True}]

    @pytest.mark.asyncio
    async def test_rest_set_power_off(self):
        """Test REST adapter sends power OFF command."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [], "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            result = await adapter.set_power("192.168.1.100", "test_psk", False)

            assert result is True
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["params"] == [{"status": False}]

    @pytest.mark.asyncio
    async def test_rest_retry_on_failure(self):
        """Test REST adapter retries 3 times on failure."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            # Fail twice, succeed on third attempt
            mock_response_error = MagicMock()
            mock_response_error.raise_for_status.side_effect = Exception("Connection error")
            mock_response_success = MagicMock()
            mock_response_success.json.return_value = {"result": [{"status": "active"}]}
            mock_response_success.raise_for_status = MagicMock()
            mock_client.post.side_effect = [
                mock_response_error,
                mock_response_error,
                mock_response_success,
            ]

            with patch("asyncio.sleep", return_value=None):  # Speed up test
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "active"
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_rest_returns_error_after_max_retries(self):
        """Test REST adapter returns 'error' after 3 failed attempts."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            # Fail all attempts
            mock_response_error = MagicMock()
            mock_response_error.raise_for_status.side_effect = Exception("Connection error")
            mock_client.post.return_value = mock_response_error

            with patch("asyncio.sleep", return_value=None):  # Speed up test
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "error"
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_rest_timeout_handling(self):
        """Test REST adapter handles timeout errors."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            import httpx

            mock_client.post.side_effect = httpx.TimeoutException("Timeout")

            with patch("asyncio.sleep", return_value=None):
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "error"

    @pytest.mark.asyncio
    async def test_rest_invalid_response_format(self):
        """Test REST adapter handles invalid JSON response."""
        from app.adapters.bravia import BraviaRestAdapter

        adapter = BraviaRestAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"invalid": "format"}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            with patch("asyncio.sleep", return_value=None):
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "error"


class TestBraviaSimpleIPAdapter:
    """Tests for BraviaSimpleIPAdapter (Simple IP Control)."""

    @pytest.mark.asyncio
    async def test_simple_ip_get_power_status_on(self):
        """Test Simple IP adapter returns 'active' for power ON."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            # Response: *SAPOWR0000000000000001\n (power ON)
            mock_reader.read.return_value = b"*SAPOWR0000000000000001\n"

            status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "active"
            mock_writer.write.assert_called_once()
            sent_data = mock_writer.write.call_args[0][0]
            assert b"*SEPOWR" in sent_data
            assert len(sent_data) == 24

    @pytest.mark.asyncio
    async def test_simple_ip_get_power_status_off(self):
        """Test Simple IP adapter returns 'standby' for power OFF."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            # Response: *SAPOWR0000000000000000\n (power OFF)
            mock_reader.read.return_value = b"*SAPOWR0000000000000000\n"

            status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "standby"

    @pytest.mark.asyncio
    async def test_simple_ip_set_power_on(self):
        """Test Simple IP adapter sends correct packet for power ON."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            mock_reader.read.return_value = b"*SAPOWR0000000000000001\n"

            result = await adapter.set_power("192.168.1.100", "test_psk", True)

            assert result is True
            sent_data = mock_writer.write.call_args[0][0]
            assert sent_data == b"*SCPOWR0000000000000001\n"
            assert len(sent_data) == 24

    @pytest.mark.asyncio
    async def test_simple_ip_set_power_off(self):
        """Test Simple IP adapter sends correct packet for power OFF."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            mock_reader.read.return_value = b"*SAPOWR0000000000000000\n"

            result = await adapter.set_power("192.168.1.100", "test_psk", False)

            assert result is True
            sent_data = mock_writer.write.call_args[0][0]
            assert sent_data == b"*SCPOWR0000000000000000\n"

    @pytest.mark.asyncio
    async def test_simple_ip_connection_error(self):
        """Test Simple IP adapter handles connection errors."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_open.side_effect = ConnectionRefusedError("Connection refused")

            with patch("asyncio.sleep", return_value=None):
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "error"

    @pytest.mark.asyncio
    async def test_simple_ip_invalid_response(self):
        """Test Simple IP adapter handles invalid responses."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)
            mock_reader.read.return_value = b"INVALID_RESPONSE"

            with patch("asyncio.sleep", return_value=None):
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "error"

    @pytest.mark.asyncio
    async def test_simple_ip_retry_logic(self):
        """Test Simple IP adapter retries on failure."""
        from app.adapters.bravia import BraviaSimpleIPAdapter

        adapter = BraviaSimpleIPAdapter()

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            # Fail twice, succeed on third
            mock_open.side_effect = [
                ConnectionRefusedError("Connection refused"),
                ConnectionRefusedError("Connection refused"),
                (mock_reader, mock_writer),
            ]
            mock_reader.read.return_value = b"*SAPOWR0000000000000001\n"

            with patch("asyncio.sleep", return_value=None):
                status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "active"
            assert mock_open.call_count == 3


class TestBraviaAdapter:
    """Tests for BraviaAdapter (facade with fallback logic)."""

    @pytest.mark.asyncio
    async def test_facade_uses_rest_when_available(self):
        """Test facade uses REST API when it succeeds."""
        from app.adapters.bravia import BraviaAdapter

        adapter = BraviaAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"status": "active"}]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            status = await adapter.get_power_status("192.168.1.100", "test_psk")

            assert status == "active"
            # Should only call REST (not Simple IP)
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_facade_fallback_to_simple_ip(self):
        """Test facade falls back to Simple IP when REST fails."""
        from app.adapters.bravia import BraviaAdapter

        adapter = BraviaAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            # REST fails
            import httpx

            mock_client.post.side_effect = httpx.TimeoutException("Timeout")

            with patch("asyncio.open_connection") as mock_open:
                mock_reader = AsyncMock()
                mock_writer = AsyncMock()
                mock_open.return_value = (mock_reader, mock_writer)
                # Simple IP succeeds
                mock_reader.read.return_value = b"*SAPOWR0000000000000001\n"

                with patch("asyncio.sleep", return_value=None):
                    status = await adapter.get_power_status("192.168.1.100", "test_psk")

                assert status == "active"
                # Should have tried REST (3 times) then Simple IP
                assert mock_client.post.call_count == 3
                mock_open.assert_called_once()

    @pytest.mark.asyncio
    async def test_facade_returns_error_when_both_fail(self):
        """Test facade returns 'error' when both protocols fail."""
        from app.adapters.bravia import BraviaAdapter

        adapter = BraviaAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            import httpx

            mock_client.post.side_effect = httpx.TimeoutException("Timeout")

            with patch("asyncio.open_connection") as mock_open:
                mock_open.side_effect = ConnectionRefusedError("Connection refused")

                with patch("asyncio.sleep", return_value=None):
                    status = await adapter.get_power_status("192.168.1.100", "test_psk")

                assert status == "error"

    @pytest.mark.asyncio
    async def test_facade_set_power_with_fallback(self):
        """Test facade set_power falls back to Simple IP."""
        from app.adapters.bravia import BraviaAdapter

        adapter = BraviaAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            import httpx

            mock_client.post.side_effect = httpx.TimeoutException("Timeout")

            with patch("asyncio.open_connection") as mock_open:
                mock_reader = AsyncMock()
                mock_writer = AsyncMock()
                mock_open.return_value = (mock_reader, mock_writer)
                mock_reader.read.return_value = b"*SAPOWR0000000000000001\n"

                with patch("asyncio.sleep", return_value=None):
                    result = await adapter.set_power("192.168.1.100", "test_psk", True)

                assert result is True
                # Should have tried REST then Simple IP
                assert mock_client.post.call_count == 3
                mock_open.assert_called_once()

    @pytest.mark.asyncio
    async def test_facade_logs_protocol_used(self, caplog):
        """Test facade logs which protocol was used."""
        import logging
        from app.adapters.bravia import BraviaAdapter

        # Ensure logs are captured
        caplog.set_level(logging.INFO, logger="app.adapters.bravia")

        adapter = BraviaAdapter()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"status": "active"}]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            await adapter.get_power_status("192.168.1.100", "test_psk")

            # Should log that REST was used
            assert any("REST" in record.message for record in caplog.records)
