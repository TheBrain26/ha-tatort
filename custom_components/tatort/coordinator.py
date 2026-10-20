"""Coordinator for fetching Tatort data."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import ARD_ASSET_URL, DOMAIN, REQUEST_TIMEOUT, TATORT_PAGE_URL
from .parser import UNKNOWN, episode_hint, parse_image_url, parse_page

_LOGGER = logging.getLogger(__name__)


class TatortCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Fetch and parse Tatort information in one coordinated update."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        *,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._session = session

    async def _async_update_data(self) -> dict[str, str]:
        """Fetch the listing page, then its image and broadcast metadata."""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with self._session.get(TATORT_PAGE_URL, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error fetching the Tatort page: {err}") from err

        data = parse_page(html)
        asset_id = data["folgen_id"]
        if asset_id == UNKNOWN:
            data["bild_api"] = UNKNOWN
            return data

        asset_url = ARD_ASSET_URL.format(asset_id=asset_id)
        try:
            async with self._session.get(asset_url, timeout=timeout) as response:
                response.raise_for_status()
                payload: dict[str, Any] = await response.json(content_type=None)
            data["bild_api"] = parse_image_url(payload)
            data["hinweis"] = episode_hint(payload, dt_util.now().date())
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            _LOGGER.warning("Could not fetch the Tatort preview metadata: %s", err)
            data["bild_api"] = UNKNOWN
        return data
