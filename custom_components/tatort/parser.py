
"""Parsing helpers for the ARD Tatort page and asset response."""

from __future__ import annotations

import html as html_lib
import re
from typing import Any

UNKNOWN = "unbekannt"


def _clean(value: str) -> str:
    """Clean extracted text."""
    value = html_lib.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n·|-–")


def parse_page(html: str) -> dict[str, str]:
    """Extract information about the featured Tatort."""

    # Read the introductory section rather than the complete
    # list of historical episodes and investigative teams.
    section = re.split(
        r"Tatort-Erstausstrahlungen|Alle Tatort-Teams",
        html,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Identify the featured investigative city.
    city = UNKNOWN
    team_heading = re.search(
        r"(?:ermittelt(?:\s+erneut)?\s+Team)\s+"
        r"([^<\"\\]{2,70})",
        section,
        re.IGNORECASE,
    )
    if team_heading:
        city = _clean(team_heading.group(1))

    # Extract the episode title.
    title = UNKNOWN
    title_match = re.search(
        r"Tatort:\s*([^\"<]+)",
        section,
        re.IGNORECASE,
    )
    if title_match:
        title = _clean(
            title_match.group(1).split("Bild:", 1)[0]
        )

    # Extract the investigative team near the featured city.
    investigator = UNKNOWN
    if city != UNKNOWN:
        team_match = re.search(
            r"([^\"<>]{2,100})\s*·\s*"
            + re.escape(city)
            + r"(?=[\"<]|$)",
            section,
            re.IGNORECASE,
        )
        if team_match:
            investigator = _clean(team_match.group(1))

    # Extract the episode identifier.
    episode_match = re.search(
        r"/video/tatort/[^\"/]+/[^\"/]+/([^\"?/]+)",
        section,
    )

    episode_id = (
        episode_match.group(1).strip()
        if episode_match
        else UNKNOWN
    )

    # A featured episode is not the same as a currently
    # available stream. Keep the existing status values.
    available = "ermittelt Team" in section

    return {
        "aktuell": (
            "verfuegbar" if available else "kein_tatort"
        ),
        "stadt": city,
        "titel": title,
        "ermittler": investigator,
        "folgen_id": episode_id,
    }


def parse_image_url(payload: dict[str, Any]) -> str:
    """Return the episode image URL."""

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
