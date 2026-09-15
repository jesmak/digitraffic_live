"""Train data interpretation and feed building."""

from __future__ import annotations

import re
from datetime import timedelta

from homeassistant.util import dt as dt_util

from custom_components.digitraffic_live.geo import Area
from custom_components.digitraffic_live.texts import load_texts
from custom_components.digitraffic_live.trains import (
    TrainFeedConfig,
    build_train_features,
    build_train_query,
    composition_details,
    delay_minutes,
    format_clock,
    passenger_notice_index,
    station_name,
    train_label,
)

from .conftest import COMPOSITION, PASSENGER_INFORMATION, running_trains


def trains() -> list[dict]:
    return running_trains()["data"]["currentlyRunningTrains"]


def config(**overrides) -> TrainFeedConfig:
    values = {"route": ("HKI", "LR"), "categories": (), "area": None, "max_age_minutes": 15}
    return TrainFeedConfig(**(values | overrides))


def test_query_without_filters() -> None:
    assert build_train_query().startswith("{ currentlyRunningTrains {")


def test_route_stations_are_combined_with_and() -> None:
    query = build_train_query(route=["HKI", "LR"])
    assert "(where: {and: [" in query
    assert 'equals: "HKI"' in query
    assert 'equals: "LR"' in query


def test_categories_are_combined_with_or() -> None:
    assert "where: {or: [" in build_train_query(categories=["Long-distance", "Commuter"])
    assert '(where: {trainType: {trainCategory: {name: {equals: "Cargo"}}}})' in build_train_query(categories=["Cargo"])


def test_query_values_are_escaped() -> None:
    assert 'equals: "A\\"B"' in build_train_query(route=['A"B', "C"])
    assert 'equals: "KÖK"' in build_train_query(route=["KÖK", "C"])


def test_train_helpers() -> None:
    train = trains()[0]
    assert delay_minutes(train) == 11
    assert delay_minutes({**train, "last": []}) == 11
    assert delay_minutes({**train, "last": [], "next": []}) is None
    assert station_name("Helsinki asema") == "Helsinki"
    assert train_label(train) == "IC 8"


def test_clock_follows_the_language() -> None:
    assert re.fullmatch(r"\d\d\.\d\d", format_clock("2026-09-14T18:04:00Z", "fi"))
    assert re.fullmatch(r"\d\d:\d\d", format_clock("2026-09-14T18:04:00Z", "en"))
    assert format_clock(None, "fi") == ""


def test_passenger_notices_are_indexed_by_train() -> None:
    messages = [
        *PASSENGER_INFORMATION,
        {"trainNumber": 8, "trainDepartureDate": "2026-09-14", "audio": {"text": {"fi": "Myöhässä"}}},
        {"stations": ["LR"], "video": {"text": {"fi": "Asematiedote"}}},
    ]
    assert passenger_notice_index(messages, "en") == {"8|2026-09-14": ["Delayed by track works.", "Myöhässä"]}
    assert passenger_notice_index("not a list", "en") == {}


def test_composition_details() -> None:
    assert composition_details(COMPOSITION, load_texts("en")) == [
        {"label": "Train", "value": "5 cars · max 200 km/h · restaurant, pets"}
    ]
    assert composition_details(None, load_texts("en")) == []


def test_features_follow_the_map_feed_format() -> None:
    notices = passenger_notice_index(PASSENGER_INFORMATION, "en")
    features = build_train_features(trains(), notices, config(), load_texts("en"), dt_util.utcnow())

    assert len(features) == 1
    feature = features[0]
    assert feature["id"] == "train:2026-09-14/8"
    assert feature["geometry"]["coordinates"] == [27.3, 60.9]
    props = feature["properties"]
    assert props["name"] == "IC 8"
    assert props["kind"] == "train.long_distance"
    assert props["badge"] == "IC 8"
    assert props["label"] == "→ Helsinki"
    assert props["subtitle"] == "Joensuu → Helsinki"
    assert props["speed_kmh"] == 113
    assert props["delay_minutes"] == 11
    assert "cancelled" not in props
    assert props["notices"] == ["Delayed by track works."]
    assert props["detail_action"] == {
        "action": "digitraffic_live.get_train_composition",
        "data": {"departure_date": "2026-09-14", "train_number": 8},
    }
    assert [detail["label"] for detail in props["details"]] == ["Passed", "Next stop"]
    assert props["details"][1]["value"].startswith("Kouvola ")
    assert props["details"][1]["value"].endswith(", track 6")


def test_old_positions_and_positions_outside_the_area_are_left_out() -> None:
    texts = load_texts("en")
    later = dt_util.utcnow() + timedelta(minutes=30)
    assert build_train_features(trains(), {}, config(), texts, later) == []

    far_away = Area(latitude=65.0, longitude=25.5, radius_km=10)
    assert build_train_features(trains(), {}, config(area=far_away), texts, dt_util.utcnow()) == []
