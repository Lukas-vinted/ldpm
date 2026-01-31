"""
Sony BRAVIA adapter modules for TV control.

This module provides three adapter classes:
1. BraviaRestAdapter - REST API control (JSON-RPC over HTTP)
2. BraviaSimpleIPAdapter - Simple IP Control (TCP binary protocol)
3. BraviaAdapter - Facade that tries REST first, falls back to Simple IP

Protocol Documentation:
- REST API: http://{ip}/sony/system with X-Auth-PSK header
- Simple IP: TCP port 20060 with 24-byte fixed packets
"""

import asyncio
import logging
from typing import Literal

import httpx

logger = logging.getLogger(__name__)

PowerStatus = Literal["active", "standby", "error"]


class BraviaRestAdapter:
    """Sony BRAVIA REST API adapter (primary control method).
    
    Uses JSON-RPC over HTTP on port 80.
    Requires Pre-Shared Key (PSK) for authentication.
    """

    def __init__(self, timeout: float = 5.0, max_retries: int = 3):
        """Initialize REST adapter.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def get_power_status(self, ip: str, psk: str) -> PowerStatus:
        """Get TV power status via REST API.
        
        Args:
            ip: TV IP address
            psk: Pre-Shared Key for authentication
            
        Returns:
            "active" if TV is on, "standby" if off, "error" on failure
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"http://{ip}/sony/system",
                        headers={"X-Auth-PSK": psk},
                        json={
                            "method": "getPowerStatus",
                            "params": [],
                            "version": "1.0",
                            "id": 1,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse response: {"result": [{"status": "active"}]}
                    if "result" in data and len(data["result"]) > 0:
                        status = data["result"][0].get("status", "").lower()
                        if status in ["active", "standby"]:
                            return status  # type: ignore
                    
                    # Invalid response format
                    logger.warning(f"Invalid response format from {ip}: {data}")
                    raise ValueError("Invalid response format")
                    
            except Exception as e:
                logger.warning(
                    f"REST get_power_status attempt {attempt + 1}/{self.max_retries} failed for {ip}: {e}"
                )
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    await asyncio.sleep(2**attempt)
                    
        return "error"

    async def set_power(self, ip: str, psk: str, on: bool) -> bool:
        """Set TV power state via REST API.
        
        Args:
            ip: TV IP address
            psk: Pre-Shared Key for authentication
            on: True to power on, False to power off
            
        Returns:
            True if command succeeded, False on failure
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"http://{ip}/sony/system",
                        headers={"X-Auth-PSK": psk},
                        json={
                            "method": "setPowerStatus",
                            "params": [{"status": on}],
                            "version": "1.0",
                            "id": 1,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Success response: {"result": [], "id": 1}
                    if "result" in data:
                        logger.info(f"REST set_power({on}) succeeded for {ip}")
                        return True
                    
                    # Error response
                    logger.warning(f"REST set_power error response from {ip}: {data}")
                    raise ValueError("Invalid response format")
                    
            except Exception as e:
                logger.warning(
                    f"REST set_power attempt {attempt + 1}/{self.max_retries} failed for {ip}: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    
        return False


class BraviaSimpleIPAdapter:
    """Sony BRAVIA Simple IP Control adapter (fallback method).
    
    Uses TCP binary protocol on port 20060.
    No authentication required.
    24-byte fixed packet format.
    """

    def __init__(self, port: int = 20060, timeout: float = 5.0, max_retries: int = 3):
        """Initialize Simple IP adapter.
        
        Args:
            port: TCP port (default 20060)
            timeout: Socket timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_packet(self, command: str, code: str, value: str) -> bytes:
        """Build 24-byte Simple IP Control packet.
        
        Args:
            command: Command type (*SC=set, *SE=enquiry)
            code: Feature code (e.g., POWR)
            value: Value string (padded with #)
            
        Returns:
            24-byte packet ending with newline
        """
        # Format: {command}{code}{value}\n
        # Total length must be 24 bytes
        packet = f"{command}{code}{value}"
        # Pad with # to reach 23 bytes, then add \n
        packet = packet.ljust(23, "#") + "\n"
        return packet.encode("ascii")

    def _parse_response(self, data: bytes) -> tuple[str, str, str]:
        """Parse Simple IP Control response packet.
        
        Args:
            data: Raw response bytes
            
        Returns:
            Tuple of (command, code, value)
        """
        response = data.decode("ascii").strip()
        # Format: *SAPOWR0000000000000001
        if len(response) < 8:
            raise ValueError("Response too short")
        
        command = response[:3]  # *SA
        code = response[3:7]  # POWR
        value = response[7:].rstrip("#")  # Remove padding
        
        return command, code, value

    async def get_power_status(self, ip: str, psk: str) -> PowerStatus:
        """Get TV power status via Simple IP Control.
        
        Args:
            ip: TV IP address
            psk: Not used (Simple IP has no auth)
            
        Returns:
            "active" if TV is on, "standby" if off, "error" on failure
        """
        for attempt in range(self.max_retries):
            try:
                # Open TCP connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, self.port),
                    timeout=self.timeout,
                )
                
                try:
                    # Send enquiry packet: *SEPOWR#################\n
                    packet = self._build_packet("*SE", "POWR", "")
                    writer.write(packet)
                    await writer.drain()
                    
                    # Read response
                    data = await asyncio.wait_for(
                        reader.read(1024),
                        timeout=self.timeout,
                    )
                    
                    # Parse response: *SAPOWR0000000000000001\n
                    command, code, value = self._parse_response(data)
                    
                    if command == "*SA" and code == "POWR":
                        # Value: 0000000000000001 = ON, 0000000000000000 = OFF
                        if value.endswith("1"):
                            return "active"
                        elif value.endswith("0"):
                            return "standby"
                    
                    raise ValueError(f"Invalid response: {data}")
                    
                finally:
                    writer.close()
                    await writer.wait_closed()
                    
            except Exception as e:
                logger.warning(
                    f"Simple IP get_power_status attempt {attempt + 1}/{self.max_retries} failed for {ip}: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    
        return "error"

    async def set_power(self, ip: str, psk: str, on: bool) -> bool:
        """Set TV power state via Simple IP Control.
        
        Args:
            ip: TV IP address
            psk: Not used (Simple IP has no auth)
            on: True to power on, False to power off
            
        Returns:
            True if command succeeded, False on failure
        """
        for attempt in range(self.max_retries):
            try:
                # Open TCP connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, self.port),
                    timeout=self.timeout,
                )
                
                try:
                    # Send command packet: *SCPOWR0000000000000001\n (on) or *SCPOWR0000000000000000\n (off)
                    value = "0000000000000001" if on else "0000000000000000"
                    packet = self._build_packet("*SC", "POWR", value)
                    writer.write(packet)
                    await writer.drain()
                    
                    # Read acknowledgment
                    data = await asyncio.wait_for(
                        reader.read(1024),
                        timeout=self.timeout,
                    )
                    
                    # Parse response: *SAPOWR0000000000000001\n (echoes new state)
                    command, code, response_value = self._parse_response(data)
                    
                    if command == "*SA" and code == "POWR":
                        logger.info(f"Simple IP set_power({on}) succeeded for {ip}")
                        return True
                    
                    raise ValueError(f"Invalid response: {data}")
                    
                finally:
                    writer.close()
                    await writer.wait_closed()
                    
            except Exception as e:
                logger.warning(
                    f"Simple IP set_power attempt {attempt + 1}/{self.max_retries} failed for {ip}: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    
        return False


class BraviaAdapter:
    """Facade adapter that tries REST first, falls back to Simple IP.
    
    This is the main adapter to use for TV control. It automatically
    handles protocol selection and fallback.
    """

    def __init__(self):
        """Initialize facade adapter with REST and Simple IP adapters."""
        self.rest = BraviaRestAdapter()
        self.simple_ip = BraviaSimpleIPAdapter()

    async def get_power_status(self, ip: str, psk: str | None) -> PowerStatus:
        """Get TV power status (tries REST first, falls back to Simple IP).
        
        Args:
            ip: TV IP address
            psk: Pre-Shared Key for REST authentication (None = skip REST, use Simple IP only)
            
        Returns:
            "active" if TV is on, "standby" if off, "error" on failure
        """
        if psk:
            logger.debug(f"Trying REST API for {ip}")
            status = await self.rest.get_power_status(ip, psk)
            
            if status != "error":
                logger.info(f"REST API succeeded for {ip}: {status}")
                return status
            
            logger.info(f"REST API failed for {ip}, falling back to Simple IP")
        else:
            logger.debug(f"No PSK provided for {ip}, using Simple IP only")
        
        status = await self.simple_ip.get_power_status(ip, psk or "")
        
        if status != "error":
            logger.info(f"Simple IP succeeded for {ip}: {status}")
        else:
            logger.error(f"Both protocols failed for {ip}" if psk else f"Simple IP failed for {ip}")
        
        return status

    async def set_power(self, ip: str, psk: str | None, on: bool) -> bool:
        """Set TV power state (tries REST first, falls back to Simple IP).
        
        Args:
            ip: TV IP address
            psk: Pre-Shared Key for REST authentication (None = skip REST, use Simple IP only)
            on: True to power on, False to power off
            
        Returns:
            True if command succeeded, False on failure
        """
        if psk:
            logger.debug(f"Trying REST API set_power({on}) for {ip}")
            success = await self.rest.set_power(ip, psk, on)
            
            if success:
                logger.info(f"REST API set_power({on}) succeeded for {ip}")
                return True
            
            logger.info(f"REST API set_power failed for {ip}, falling back to Simple IP")
        else:
            logger.debug(f"No PSK provided for {ip}, using Simple IP only")
        
        success = await self.simple_ip.set_power(ip, psk or "", on)
        
        if success:
            logger.info(f"Simple IP set_power({on}) succeeded for {ip}")
        else:
            logger.error(f"Both protocols failed for {ip} set_power({on})" if psk else f"Simple IP failed for {ip} set_power({on})")
        
        return success
