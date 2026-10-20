"""Tests for the standalone Tatort parsing helpers."""

from datetime import date
import importlib.util
from pathlib import Path
import unittest


PARSER_PATH = Path(__file__).parents[1] / "custom_components" / "tatort" / "parser.py"
SPEC = importlib.util.spec_from_file_location("tatort_parser", PARSER_PATH)
assert SPEC and SPEC.loader
parser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parser)


class TatortParserTests(unittest.TestCase):
    def test_parse_page_extracts_existing_fields(self):
        html = (
            '<a href="/video/tatort/abc/def/episode-123">'
            'Tatort: Der Testfall (2026) · Bild: ARD</a>'
            'ermittelt Team Frankfurt · <span>Anna Beispiel · Frankfurt</span>'
        )
        data = parser.parse_page(html)
        self.assertEqual(data["aktuell"], "Sonntag Tatort")
        self.assertEqual(data["stadt"], "Frankfurt")
        self.assertEqual(data["titel"], "Der Testfall (2026)")
        self.assertEqual(data["ermittler"], "Anna Beispiel")
        self.assertEqual(data["folgen_id"], "episode-123")

    def test_parse_page_handles_missing_tatort(self):
        data = parser.parse_page("Keine aktuelle Tatort-Folge")
        self.assertEqual(data["aktuell"], "Sonntag kein Tatort")
        self.assertEqual(data["stadt"], "unbekannt")
        self.assertEqual(data["folgen_id"], "unbekannt")

    def test_episode_hint_uses_future_broadcast_date(self):
        payload = {
            "teaser": {
                "broadcastedOn": "2026-10-25T18:15:00Z",
            }
        }
        self.assertEqual(
            parser.episode_hint(payload, today=date(2026, 10, 20)),
            "Nächster Tatort",
        )

    def test_episode_hint_falls_back_to_last_for_past_or_missing_date(self):
        self.assertEqual(
            parser.episode_hint(
                {"broadcastedOn": "2026-10-18T18:15:00Z"},
                today=__import__("datetime").date(2026, 10, 20),
            ),
            "Letzter Tatort",
        )
        self.assertEqual(
            parser.episode_hint({}, today=__import__("datetime").date(2026, 10, 20)),
            "Letzter Tatort",
        )

    def test_parse_image_url(self):
        payload = {
            "mediaCollection": {
                "embedded": {"meta": {"images": [{"url": "https://example.org/image.jpg"}]}}
            }
        }
        self.assertEqual(parser.parse_image_url(payload), "https://example.org/image.jpg")


if __name__ == "__main__":
    unittest.main()
