"""Feed texts and Map Feed building blocks."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from custom_components.digitraffic_live.const import LANGUAGES
from custom_components.digitraffic_live.feed import iso_from_epoch_ms, point_feature, row
from custom_components.digitraffic_live.ships import ship_details
from custom_components.digitraffic_live.texts import TEXTS_DIR, load_texts
from custom_components.digitraffic_live.traffic_messages import join_quantity

TRANSLATIONS_DIR = Path(TEXTS_DIR).parent / "translations"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def placeholders(text: str) -> list[str]:
    return sorted(re.findall(r"\{(\w+)\}", text))


def flatten(tree: dict, prefix: str = "") -> dict[str, str]:
    result = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            result |= flatten(value, f"{prefix}{key}.")
        else:
            result[f"{prefix}{key}"] = value
    return result


@pytest.mark.parametrize("language", LANGUAGES)
def test_feed_texts_match_english(language: str) -> None:
    english = read(TEXTS_DIR / "en.json")
    texts = read(TEXTS_DIR / f"{language}.json")
    assert texts.keys() == english.keys()
    for key, text in english.items():
        assert placeholders(texts[key]) == placeholders(text), key
        assert texts[key].strip(), key


@pytest.mark.parametrize("language", LANGUAGES)
def test_ui_translations_match_english(language: str) -> None:
    english = flatten(read(TRANSLATIONS_DIR / "en.json"))
    translation = flatten(read(TRANSLATIONS_DIR / f"{language}.json"))
    assert translation.keys() == english.keys()
    for key, text in english.items():
        assert placeholders(translation[key]) == placeholders(text), key


def test_texts_fill_placeholders_and_fall_back_to_english() -> None:
    assert load_texts("fi")("cars", n=5) == "5 vaunua"
    assert load_texts("de")("cars", n=5) == "5 cars"
    assert load_texts("en")("no_such_key") == "no_such_key"


@pytest.mark.parametrize(
    ("language", "value", "decimals", "text"),
    [
        ("en", 2.5, 1, "2.5"),
        ("fi", 2.5, 1, "2,5"),
        ("fi", 3.0, 1, "3"),
        ("en", 3.0, 1, "3"),
        ("fi", 12.25, 2, "12,25"),
        ("de", 2.5, 1, "2.5"),
    ],
)
def test_numbers_are_written_in_the_feeds_language(language: str, value: float, decimals: int, text: str) -> None:
    assert load_texts(language).number(value, decimals) == text


def test_a_ships_draught_and_a_restrictions_quantity_in_finnish() -> None:
    finnish = load_texts("fi")
    [draught] = [detail for detail in ship_details({}, {"draught": 75}, "cargo", finnish) if detail["label"] == finnish("draught")]
    assert draught["value"] == "7,5"
    assert join_quantity("Ajoneuvon korkeus", 4.4, "m", finnish) == "Ajoneuvon korkeus 4,4 m"


def test_point_feature_rounds_and_drops_empty_properties() -> None:
    feature = point_feature(
        "ship:1",
        60.1234567,
        27.7654321,
        {"name": "A", "heading": None, "notices": [], "footer": "", "stationary": False},
    )
    assert feature == {
        "type": "Feature",
        "id": "ship:1",
        "geometry": {"type": "Point", "coordinates": [27.76543, 60.12346]},
        "properties": {"name": "A", "stationary": False},
    }


def test_rows_and_times() -> None:
    assert row("Draught", 2.2, "m") == {"label": "Draught", "value": 2.2, "unit": "m"}
    assert row("Type", "Tug") == {"label": "Type", "value": "Tug"}
    assert iso_from_epoch_ms(0) == "1970-01-01T00:00:00+00:00"
    assert iso_from_epoch_ms(None) is None
