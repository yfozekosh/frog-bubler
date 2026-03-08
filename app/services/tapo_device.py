"""Tapo smart plug device control module.

This module provides async functions to interact with Tapo P110 smart plugs:
- Device connection with retry logic and rate limiting
- Plug control (on/off) with activity logging
- Error handling and connection management
"""

import asyncio
import time
from typing import Any

from tapo import ApiClient

from app.config import PLUG_IPS, REQUEST_COOLDOWN, TAPO_PASSWORD, TAPO_USERNAME
from app.storage.data_manager import add_activity_log

# Rate limiting - track last request time per plug
last_request_time = {"1": 0.0, "2": 0.0}


async def get_device(plug_id, retries=3) -> Any:
    """Get a Tapo device connection with retry logic and rate limiting.

    Args:
        plug_id (str): ID of the plug to connect to (e.g., "1" or "2").
        retries (int, optional): Number of connection attempts. Defaults to 3.

    Returns:
        P110Device: Connected Tapo device instance, or None if credentials
                    are not configured.

    Raises:
        ValueError: If plug_id is invalid.
        Exception: If all retry attempts fail.
    """
    ip = PLUG_IPS.get(plug_id)
    if not ip:
        raise ValueError(f"Invalid plug_id: {plug_id}")

    # Rate limiting
    now = time.time()
    time_since_last = now - last_request_time.get(plug_id, 0)
    if time_since_last < REQUEST_COOLDOWN:
        await asyncio.sleep(REQUEST_COOLDOWN - time_since_last)

    last_request_time[plug_id] = time.time()

    if TAPO_USERNAME is None or TAPO_PASSWORD is None:
        raise RuntimeError("TAPO credentials not configured (TAPO_USERNAME/TAPO_PASSWORD)")

    # Retry logic
    for attempt in range(retries):
        try:
            client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
            device = await client.p110(ip)
            return device
        except Exception as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 1
                print(
                    f"Attempt {attempt + 1} failed for plug {plug_id}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                print(f"All retry attempts failed for plug {plug_id}")
                raise


async def turn_on_plug(plug_id, source="manual", device_info=None):
    """Turn on a Tapo smart plug and log the activity.

    Args:
        plug_id (str): ID of the plug to turn on.
        source (str, optional): Source of the action. Defaults to "manual".
        device_info (str, optional): Information about the device/user.
                                     Defaults to None.
    """
    device = await get_device(plug_id)
    if device is None:
        print(f"Cannot get device to turn on device {plug_id}")
        return
    await device.on()
    add_activity_log(plug_id, "on", source, device_info)


async def turn_off_plug(plug_id, source="manual", device_info=None):
    """Turn off a Tapo smart plug and log the activity.

    Args:
        plug_id (str): ID of the plug to turn off.
        source (str, optional): Source of the action. Defaults to "manual".
        device_info (str, optional): Information about the device/user.
                                     Defaults to None.
    """
    device = await get_device(plug_id)
    if device is None:
        print(f"Cannot get device to turn off device {plug_id}")
        return
    await device.off()
    add_activity_log(plug_id, "off", source, device_info)
