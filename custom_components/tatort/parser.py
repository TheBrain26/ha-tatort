"""Parsing helpers for the ARD Tatort page and asset response."""

from __future__ import annotations

import re
from typing import Any

UNKNOWN = "unbekannt"


def parse_page(html: str) -> dict[str, str]:
    """Extract the fields used by the existing REST sensors."""
    available = "ermittelt Team" in html
    city = UNKNOWN
    if available:
        city_match = re.search(r'ermittelt Team([^"<>]*)', html)
        if city_match:
            city = city_match.group(1).rstrip(" ·-|").strip() or UNKNOWN

    title = UNKNOWN
    title_match = re.search(r'Tatort: ([^"<]+)', html)
    if title_match:
        title = title_match.group(1).split("Bild:", 1)[0].rstrip(" ·-|").strip() or UNKNOWN

    investigator = UNKNOWN
    if city != UNKNOWN:
        investigator_match = re.search(
            rf'([^"<>]{{2,60}}) · {re.escape(city)}', html
        )
        if investigator_match:
            investigator = investigator_match.group(1).strip() or UNKNOWN

    episode_id_match = re.search(
        r'/video/tatort/[^"/]+/[^"/]+/([^"?/]+)', html
    )

    return {
        "aktuell": "verfuegbar" if available else "kein_tatort",
        "stadt": city,
        "titel": title,
        "ermittler": investigator,
        "folgen_id": episode_id_match.group(1).strip() if episode_id_match else UNKNOWN,
    }


def parse_image_url(payload: dict[str, Any]) -> str:
    """Return the first episode image URL from the ARD asset response."""
    try:
        images = payload["mediaCollection"]["embedded"]["meta"]["images"]
    except (KeyError, TypeError):
        images = None

    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            url = first.get("url")
            if isinstance(url, str) and url:
                return url
            aspect = first.get("aspect16x9")
            if isinstance(aspect, dict):
                src = aspect.get("src")
                if isinstance(src, str) and src:
                    return src.replace("{width}", "1280")

    return UNKNOWN
