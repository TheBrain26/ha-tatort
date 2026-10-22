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

FETCH_ATTEMPTS = 3
RETRY_DELAY = 5


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

    async def _fetch(self, url: str, *, as_json: bool = False) -> Any:
        """Fetch a URL with a timeout and limited retries."""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        for attempt in range(1, FETCH_ATTEMPTS + 1):
            try:
                async with self._session.get(url, timeout=timeout) as response:
                    response.raise_for_status()
                    if as_json:
                        payload = await response.json(content_type=None)
                        if not isinstance(payload, dict):
                            raise ValueError("ARD metadata is not a JSON object")
                        return payload
                    return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                if attempt == FETCH_ATTEMPTS:
                    raise
                _LOGGER.debug(
                    "Tatort fetch attempt %s/%s failed (%s: %s); "
                    "retrying in %s seconds",
                    attempt, FETCH_ATTEMPTS, type(err).__name__, err, RETRY_DELAY,
                )
                await asyncio.sleep(RETRY_DELAY)
        raise RuntimeError("Tatort fetch finished without a result")

    async def _async_update_data(self) -> dict[str, str]:
        """Fetch metadata and retain previous data on temporary errors."""
        previous = self.data or {}
        try:
            html = await self._fetch(TATORT_PAGE_URL)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            error = f"{type(err).__name__}: {err}"
            if previous:
                _LOGGER.warning(
                    "Tatort page fetch failed after %s attempts; "
                    "retaining previous data: %s",
                    FETCH_ATTEMPTS, error,
                )
                return dict(previous)
            raise UpdateFailed(
                f"Error fetching the Tatort page after "
                f"{FETCH_ATTEMPTS} attempts: {error}"
            ) from err

        data = parse_page(html)
        if (
            data["folgen_id"] == UNKNOWN
            and data["stadt"] == UNKNOWN
            and "Tatort-Erstausstrahlungen" not in html
            and "Alle Tatort-Teams" not in html
        ):
            if previous:
                _LOGGER.warning("Unrecognized Tatort page; retaining previous data")
                return dict(previous)
            raise UpdateFailed("ARD returned an unrecognized Tatort page")
        asset_id = data["folgen_id"]
        if asset_id == UNKNOWN:
            data["bild_api"] = UNKNOWN
            return data

        asset_url = ARD_ASSET_URL.format(asset_id=asset_id)
        try:
            payload = await self._fetch(asset_url, as_json=True)
            data["bild_api"] = parse_image_url(payload)
            data["hinweis"] = episode_hint(payload, dt_util.now().date())
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            _LOGGER.warning(
                "Tatort preview metadata fetch failed after %s attempts: %s: %s",
                FETCH_ATTEMPTS, type(err).__name__, err,
            )
            if previous.get("folgen_id") == asset_id:
                data["bild_api"] = previous.get("bild_api", UNKNOWN)
                data["hinweis"] = previous.get(
                    "hinweis", data.get("hinweis", "Letzter Tatort"),
                )
            else:
                data["bild_api"] = UNKNOWN
        return data
