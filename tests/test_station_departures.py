"""A railway station's departures, in the departures format."""

from __future__ import annotations

from homeassistant.util import dt as dt_util

from custom_components.digitraffic_live.station_departures import (
    StationDeparturesConfig,
    build_departures,
    station_name_index,
)
from custom_components.digitraffic_live.texts import load_texts
from custom_components.digitraffic_live.trains import passenger_notices

from .conftest import STATION_TRAINS, STATIONS

NAMES = station_name_index(STATIONS) | {"KV": "Kouvola"}


def departures(language: str = "fi", **values: object) -> list[dict]:
    config = StationDeparturesConfig.from_data({"station": "LR", "departures": 5} | values)
    return build_departures(STATION_TRAINS, config, NAMES, {}, load_texts(language))


def test_departures_are_in_order_of_their_estimates_and_gone_ones_are_left_out() -> None:
    assert [departure["line"] for departure in departures()] == ["IC 101", "R", "S 103", "IC 105"]
    assert len(departures(departures=2)) == 2


def test_a_late_train_has_its_estimate_delay_track_and_reason() -> None:
    assert departures()[0] == {
        "id": "train:2026-10-04/101",
        "line": "IC 101",
        "mode": "train",
        "headsign": "Helsinki",
        "scheduled": "2026-10-04T14:41:00+00:00",
        "estimated": "2026-10-04T14:48:00+00:00",
        "realtime": True,
        "delay": 420,
        "platform": "1",
        "notice": "Kalustovika",
    }


def test_a_cancelled_train_stays_with_the_reason_from_anywhere_on_its_route() -> None:
    cancelled = departures("en")[2]
    assert cancelled["cancelled"] is True
    assert cancelled["notice"] == "Track work"
    assert cancelled["platform"] == "2"


def test_commuter_trains_use_their_line_letter_and_timetable_times_have_no_delay() -> None:
    commuter, later = departures()[1], departures()[3]
    assert (commuter["line"], commuter["headsign"], commuter["realtime"]) == ("R", "Kouvola", True)
    assert "notice" not in commuter and "platform" not in commuter and "cancelled" not in commuter
    assert (later["realtime"], later["delay"], later["estimated"]) == (False, 0, later["scheduled"])


def test_stops_at_keeps_only_trains_that_stop_there_later_and_fetches_more() -> None:
    config = StationDeparturesConfig.from_data({"station": "LR", "stops_at": "HKI", "departures": 5})
    assert config.fetch_count == 10
    assert StationDeparturesConfig.from_data({"station": "LR"}).fetch_count == 5
    assert [departure["line"] for departure in departures(stops_at="HKI")] == ["IC 101", "S 103", "IC 105"]


def test_only_passenger_trains_are_listed() -> None:
    cargo = STATION_TRAINS[0] | {"trainNumber": 60001, "trainType": "T", "trainCategory": "Cargo"}
    config = StationDeparturesConfig.from_data({"station": "LR", "stops_at": "HKI"})
    assert [d["line"] for d in build_departures([cargo, *STATION_TRAINS], config, NAMES, {}, load_texts("fi"))][
        0
    ] == "IC 101"


def test_station_names_lose_the_asema() -> None:
    assert NAMES["HKI"] == "Helsinki"
    assert NAMES["LR"] == "Lappeenranta"


def test_a_train_that_has_caught_up_tells_no_reason_and_its_delay_comes_from_the_times() -> None:
    row = STATION_TRAINS[0]["timeTableRows"][0] | {
        "liveEstimateTime": "2026-10-04T14:41:40.000Z",
        "differenceInMinutes": 1,
    }
    train = STATION_TRAINS[0] | {"timeTableRows": [row, *STATION_TRAINS[0]["timeTableRows"][1:]]}
    config = StationDeparturesConfig.from_data({"station": "LR"})
    departure = build_departures([train], config, NAMES, {}, load_texts("fi"))[0]
    assert departure["delay"] == 40
    assert "notice" not in departure


def test_a_trains_own_passenger_notice_comes_before_its_cause() -> None:
    config = StationDeparturesConfig.from_data({"station": "LR"})
    notices = {"101|2026-10-04": ["Passengers are directed to train S 103."]}
    departure = build_departures(STATION_TRAINS, config, NAMES, notices, load_texts("en"))[0]
    assert departure["notice"] == "Passengers are directed to train S 103."


def test_station_notices_count_only_within_their_validity() -> None:
    def message(stations: list[str], start: str, end: str, text: str) -> dict:
        return {"stations": stations, "startValidity": start, "endValidity": end, "video": {"text": {"fi": text}}}

    notices = passenger_notices(
        [
            message(["LR", "IMR"], "2026-10-02T00:00:00Z", "2026-10-05T20:59:00Z", "Junat korvataan busseilla."),
            message(["LR"], "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z", "Eilinen."),
            message(["HKI"], "2026-10-02T00:00:00Z", "2026-10-05T00:00:00Z", "Muualla."),
            {
                "trainNumber": 7,
                "trainDepartureDate": "2026-10-04",
                "stations": ["LR"],
                "video": {"text": {"fi": "Junan oma."}},
            },
        ],
        "fi",
    )
    now = dt_util.parse_datetime("2026-10-04T12:00:00Z")
    assert notices.for_station("LR", now) == ["Junat korvataan busseilla."]
    assert notices.for_station("IMR", dt_util.parse_datetime("2026-10-06T00:00:00Z")) == []
    assert notices.trains == {"7|2026-10-04": ["Junan oma."]}
