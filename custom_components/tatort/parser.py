"""Parsing helpers for the ARD Tatort page and asset response."""

from __future__ import annotations

from datetime import date, datetime, timezone
import html as html_lib
from html.parser import HTMLParser
import re
import unicodedata
from typing import Any

UNKNOWN = "unbekannt"


def _clean(value: str) -> str:
    """Clean extracted text and trailing separators."""

    value = html_lib.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = "".join(
        char
        for char in value
        if unicodedata.category(char) != "Cf"
    )
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(
        r"[\s·・•∙⋅.\-|–—]+$",
        "",
        value,
    )
    return value.strip()


class _PageText(HTMLParser):
    """Collect rendered text and linked video titles, excluding scripts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.videos = []
        self.hidden = 0
        self.href = None
        self.heading = False
        self.title = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "a":
            self.href = attrs.get("href", "")
        if tag == "h3" and self.href:
            self.heading = True
            self.title = []

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag == "h3" and self.heading:
            self.videos.append((self.href, "".join(self.title)))
            self.heading = False
        if tag == "a":
            self.href = None
        if tag in {"h2", "h3", "div", "span", "a"}:
            self.parts.append("\n")

    def handle_data(self, value):
        if not self.hidden:
            self.parts.append(value)
            if self.heading:
                self.title.append(value)


def parse_page(html: str) -> dict[str, str]:
    """Extract information about the featured Tatort."""

    page = _PageText()

    section = re.split(
        r"Tatort-Erstausstrahlungen|Alle Tatort-Teams",
        html,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    page.feed(section)

    city = UNKNOWN
    team_heading = re.search(
        r"(?:ermittelt(?:\s+erneut)?\s+Team)\s+"
        r'([^<"\\]{2,70})',
        section,
        re.IGNORECASE,
    )
    if team_heading:
        city = _clean(team_heading.group(1))

    title = UNKNOWN
    title_match = re.search(
        r'Tatort:\s*([^"<]+)',
        section,
        re.IGNORECASE,
    )
    if title_match:
        title = _clean(title_match.group(1).split("Bild:", 1)[0])

    # Modern ARD cards use h3 titles, including "Trailer: Tatort - ...".
    for href, card_title in page.videos:
        if href and "/video/tatort/" in href:
            title = _clean(re.sub(
                r"^(?:Trailer:\s*)?Tatort\s*[:–—-]\s*",
                "", card_title, flags=re.IGNORECASE,
            ))
            break

    investigator = UNKNOWN
    if city != UNKNOWN:
        team_match = re.search(
            r'([^"<>]{2,100})\s*·\s*'
            + re.escape(city)
            + r'(?=["<]|$)',
            section,
            re.IGNORECASE,
        )
        if team_match:
            investigator = _clean(team_match.group(1))

    if investigator == UNKNOWN and city != UNKNOWN:
        # The current team is listed under "Alle Tatort-Teams", outside
        # the featured section. Match the exact city to avoid other teams.
        full_page = _PageText()
        full_page.feed(html)
        text = "".join(full_page.parts)
        team = re.search(
            r"([^\n]{2,100}?)\s*·\s*" + re.escape(city) + r"\s*(?=\n|$)",
            text, re.IGNORECASE,
        )
        if team:
            investigator = _clean(team.group(1))

    episode_match = re.search(
        r'/video/tatort/[^"/]+/[^"/]+/([^"?/]+)',
        section,
    )
    episode_id = (
        episode_match.group(1).strip()
        if episode_match
        else UNKNOWN
    )

    available = team_heading is not None

    return {
        "aktuell": (
            "Sonntag Tatort"
            if available
            else "Sonntag kein Tatort"
        ),
        "hinweis": "Letzter Tatort",
        "stadt": city,
        "titel": title,
        "ermittler": investigator,
        "folgen_id": episode_id,
    }


def _parse_broadcasted_on(value: Any) -> date | None:
    """Parse an ARD broadcast date from common API value formats."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        # ARD timestamps may be expressed in seconds or milliseconds.
        timestamp = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    try:
        return datetime.fromisoformat(
            candidate.replace("Z", "+00:00")
        ).date()
    except ValueError:
        pass

    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(candidate[:10], date_format).date()
        except ValueError:
            continue
    return None


def _find_broadcast_date(value: Any) -> date | None:
    """Find broadcastedOn recursively in an ARD asset payload."""

    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in {"broadcastedon", "broadcast_date"}:
                result = _parse_broadcasted_on(item)
                if result is not None:
                    return result
        for item in value.values():
            result = _find_broadcast_date(item)
            if result is not None:
                return result
    elif isinstance(value, list):
        for item in value:
            result = _find_broadcast_date(item)
            if result is not None:
                return result
    return None


def episode_hint(payload: dict[str, Any], today: date) -> str:
    """Label the featured episode as next or last using its ARD air date."""

    broadcast_date = _find_broadcast_date(payload)
    if broadcast_date is not None and broadcast_date >= today:
        return "Nächster Tatort"
    return "Letzter Tatort"


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
