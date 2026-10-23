"""A railway station's departures and arrivals, in the departures format."""

from __future__ import annotations

import pytest
from homeassistant.util import dt as dt_util

from custom_components.digitraffic_live.coordinator import StationDepartures
from custom_components.digitraffic_live.station_departures import (
    StationDeparturesConfig,
    build_arrivals,
    build_departures,
    station_name_index,
)
from custom_components.digitraffic_live.texts import load_texts
from custom_components.digitraffic_live.trains import passenger_notices

from .conftest import STATION_TRAINS, STATIONS, timetable_row

NAMES = station_name_index(STATIONS) | {"KV": "Kouvola"}
# Before the fixture's first departure, so none is a minute past its time.
DEPARTURES_NOW = dt_util.parse_datetime("2026-10-04T14:00:00+00:00")


def departures(language: str = "fi", **values: object) -> list[dict]:
    config = StationDeparturesConfig.from_data({"station": "LR", "departures": 5} | values)
    return build_departures(STATION_TRAINS, config, NAMES, {}, load_texts(language), DEPARTURES_NOW)


def test_departures_are_in_order_of_their_estimates_and_gone_ones_are_left_out() -> None:
    assert [departure["line"] for departure in departures()] == ["IC 101", "R", "S 103", "IC 105", "IC 7"]
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


def test_stops_at_keeps_only_trains_that_stop_there_later_and_twice_the_count_is_fetched() -> None:
    config = StationDeparturesConfig.from_data({"station": "LR", "stops_at": "HKI", "departures": 5})
    assert config.fetch_count == 10
    assert StationDeparturesConfig.from_data({"station": "LR"}).fetch_count == 10
    assert [departure["line"] for departure in departures(stops_at="HKI")] == ["IC 101", "S 103", "IC 105"]


# A departure is listed until a minute past its estimated time, as departures-card shows it. Digitraffic keeps a train
# that hasn't left, a cancelled one among them, for up to an hour past its time, and such a row would take a place.
@pytest.mark.parametrize(
    ("case", "scheduled", "row", "listed"),
    [
        ("half a minute past", "14:59:30", {}, True),
        ("two minutes past", "14:58:00", {}, False),
        ("cancelled 40 minutes ago", "14:20:00", {"cancelled": True}, False),
        ("cancelled, still to leave", "15:05:00", {"cancelled": True}, True),
        ("late, still to leave", "14:50:00", {"liveEstimateTime": "2026-10-04T15:03:00.000Z"}, True),
    ],
)
def test_a_departure_is_listed_until_a_minute_past_its_time(case: str, scheduled: str, row: dict, listed: bool) -> None:
    trains = [
        train(
            1,
            [
                timetable_row("LR", "DEPARTURE", f"2026-10-04T{scheduled}.000Z", **row),
                timetable_row("HKI", "ARRIVAL", "2026-10-04T17:00:00.000Z"),
            ],
        )
    ]
    config = StationDeparturesConfig.from_data({"station": "LR", "departures": 5})
    assert len(build_departures(trains, config, NAMES, {}, load_texts("fi"), ARRIVALS_NOW)) == (1 if listed else 0), case


def test_only_passenger_trains_are_listed() -> None:
    cargo = STATION_TRAINS[0] | {"trainNumber": 60001, "trainType": "T", "trainCategory": "Cargo"}
    config = StationDeparturesConfig.from_data({"station": "LR", "stops_at": "HKI"})
    assert [d["line"] for d in build_departures([cargo, *STATION_TRAINS], config, NAMES, {}, load_texts("fi"), DEPARTURES_NOW)][
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
    departure = build_departures([train], config, NAMES, {}, load_texts("fi"), DEPARTURES_NOW)[0]
    assert departure["delay"] == 40
    assert "notice" not in departure


def test_a_trains_own_passenger_notice_comes_before_its_cause() -> None:
    config = StationDeparturesConfig.from_data({"station": "LR"})
    notices = {"101|2026-10-04": ["Passengers are directed to train S 103."]}
    departure = build_departures(STATION_TRAINS, config, NAMES, notices, load_texts("en"), DEPARTURES_NOW)[0]
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


# Arrivals: made-up trains reaching Lappeenranta at 15:00, shaped like the railway API's answer.
ARRIVALS_NOW = dt_util.parse_datetime("2026-10-04T15:00:00+00:00")


def train(number: int, rows: list[dict], **extra: object) -> dict:
    return (
        {"trainNumber": number, "departureDate": "2026-10-04", "trainType": "IC", "trainCategory": "Long-distance"}
        | {
            "cancelled": False,
            "timeTableRows": rows,
        }
        | extra
    )


def through(number: int, arrival: str, **row: object) -> dict:
    """A train from Helsinki through Lappeenranta to Joensuu, arriving at `arrival` and leaving two minutes later."""
    return train(
        number,
        [
            timetable_row("HKI", "DEPARTURE", "2026-10-04T12:00:00.000Z"),
            timetable_row("LR", "ARRIVAL", arrival, commercialTrack="001", **row),
            timetable_row("LR", "DEPARTURE", arrival.replace(":00.000Z", ":02.000Z")),
            timetable_row("JNS", "ARRIVAL", "2026-10-04T18:00:00.000Z"),
        ],
    )


def ring(number: int, first: dict, second: dict) -> dict:
    """A ring train from Lappeenranta back to it, through Kouvola twice, as the I and P trains run Helsinki to Helsinki
    through Pasila. `first` and `second` are the two arrival rows' extra fields at Kouvola."""
    return train(
        number,
        [
            timetable_row("LR", "DEPARTURE", "2026-10-04T13:50:00.000Z"),
            timetable_row("KV", "ARRIVAL", "2026-10-04T14:20:00.000Z", commercialTrack="2", **first),
            timetable_row("KV", "DEPARTURE", "2026-10-04T14:21:00.000Z"),
            timetable_row("KV", "ARRIVAL", "2026-10-04T15:10:00.000Z", commercialTrack="3", **second),
            timetable_row("KV", "DEPARTURE", "2026-10-04T15:11:00.000Z"),
            timetable_row("LR", "ARRIVAL", "2026-10-04T15:40:00.000Z", commercialTrack="1"),
        ],
        commuterLineID="R",
    )


def arrivals(trains: list[dict], count: int = 5, station: str = "LR") -> list[dict]:
    config = StationDeparturesConfig.from_data({"station": station, "departures": count, "direction": "arrivals"})
    return build_arrivals(trains, config, NAMES | {"JNS": "Joensuu"}, {}, load_texts("fi"), ARRIVALS_NOW)


def arrival(**changes: object) -> dict:
    """The whole arrival the table's IC 1 from Helsinki at 15:20 becomes, with some fields changed; None leaves one out."""
    base = {
        "id": "train-arrival:2026-10-04/1",
        "line": "IC 1",
        "mode": "train",
        "headsign": "Helsinki",
        "scheduled": "2026-10-04T15:20:00+00:00",
        "estimated": "2026-10-04T15:20:00+00:00",
        "realtime": False,
        "delay": 0,
        "platform": "1",
    }
    found = base | changes
    return {key: value for key, value in found.items() if value is not None}


# Which arrivals are listed, and everything they are listed with. One that has come in has its actual time and stays half
# an hour past it, a train that starts at the station has no arrival, and only a commercial stop counts.
@pytest.mark.parametrize(
    ("case", "trains", "expected"),
    [
        ("on its way", [through(1, "2026-10-04T15:20:00.000Z")], [arrival()]),
        (
            "late",
            [through(1, "2026-10-04T15:20:00.000Z", liveEstimateTime="2026-10-04T15:27:00.000Z", causes=[{"categoryCode": "K"}])],
            [arrival(estimated="2026-10-04T15:27:00+00:00", realtime=True, delay=420, notice="Kalustovika")],
        ),
        (
            "come in, by its actual time rather than the estimate",
            [through(1, "2026-10-04T14:50:00.000Z", liveEstimateTime="2026-10-04T14:55:00.000Z", actualTime="2026-10-04T14:52:00.000Z")],
            [arrival(scheduled="2026-10-04T14:50:00+00:00", estimated="2026-10-04T14:52:00+00:00", realtime=True, delay=120, arrived=True)],
        ),
        (
            "come in exactly half an hour ago",
            [through(1, "2026-10-04T14:30:00.000Z", actualTime="2026-10-04T14:30:00.000Z")],
            [arrival(scheduled="2026-10-04T14:30:00+00:00", estimated="2026-10-04T14:30:00+00:00", realtime=True, arrived=True)],
        ),
        ("come in 31 minutes ago", [through(1, "2026-10-04T14:29:00.000Z", actualTime="2026-10-04T14:29:00.000Z")], []),
        (
            "scheduled long ago, estimated to come",
            [through(1, "2026-10-04T14:00:00.000Z", liveEstimateTime="2026-10-04T15:05:00.000Z")],
            [arrival(scheduled="2026-10-04T14:00:00+00:00", estimated="2026-10-04T15:05:00+00:00", realtime=True, delay=3900)],
        ),
        ("cancelled", [through(1, "2026-10-04T15:20:00.000Z", cancelled=True)], [arrival(cancelled=True)]),
        (
            "starting at the station",
            [
                train(
                    1,
                    [
                        timetable_row("LR", "DEPARTURE", "2026-10-04T15:20:00.000Z"),
                        timetable_row("HKI", "ARRIVAL", "2026-10-04T17:20:00.000Z"),
                    ],
                )
            ],
            [],
        ),
        ("passing without a commercial stop", [through(1, "2026-10-04T15:20:00.000Z", commercialStop=False)], []),
        ("a cargo train", [{**through(1, "2026-10-04T15:20:00.000Z"), "trainCategory": "Cargo"}], []),
    ],
)
def test_which_arrivals_are_listed(case: str, trains: list[dict], expected: list[dict]) -> None:
    assert arrivals(trains) == expected, case


# A train through a station twice arrives by its pass still to come, or by its latest once both have come in, and a
# ring train arriving back where it started arrives from there.
@pytest.mark.parametrize(
    ("case", "station", "first", "second", "expected"),
    [
        ("the first pass come in, the second to come", "KV", {"actualTime": "2026-10-04T14:20:00.000Z"}, {}, ("15:10", "3", None)),
        ("neither come in, the first late", "KV", {"liveEstimateTime": "2026-10-04T14:55:00.000Z"}, {}, ("14:55", "2", None)),
        (
            "both come in",
            "KV",
            {"actualTime": "2026-10-04T14:20:00.000Z"},
            {"actualTime": "2026-10-04T14:50:00.000Z"},
            ("14:50", "3", True),
        ),
        ("back where it started", "LR", {}, {}, ("15:40", "1", None)),
        (
            "the first pass come in, the second late",
            "KV",
            {"actualTime": "2026-10-04T14:20:00.000Z"},
            {"liveEstimateTime": "2026-10-04T15:14:00.000Z"},
            ("15:14", "3", None),
        ),
        ("the first pass cancelled, the second to come", "KV", {"cancelled": True}, {}, ("15:10", "3", None)),
        (
            "the first pass cancelled, the second come in",
            "KV",
            {"cancelled": True},
            {"actualTime": "2026-10-04T14:58:00.000Z"},
            ("14:58", "3", True),
        ),
    ],
)
def test_a_train_through_the_station_twice_arrives_once(case: str, station: str, first: dict, second: dict, expected: tuple) -> None:
    [found] = arrivals([ring(1, first, second)], station=station)
    assert (found["estimated"][11:16], found["platform"], found.get("arrived")) == expected, case
    assert (found["line"], found["headsign"]) == ("R", "Lappeenranta"), case


def ring_passes(passes: dict[str, dict], **extra: object) -> dict:
    """The ring train from Lappeenranta through Kouvola twice, each Kouvola row's extra fields by name: arrive1 at 14:20,
    leave1 at 14:21, arrive2 at 15:10 and leave2 at 15:11."""
    rows = [
        ("LR", "DEPARTURE", "13:50", None, {}),
        ("KV", "ARRIVAL", "14:20", "2", passes.get("arrive1", {})),
        ("KV", "DEPARTURE", "14:21", "2", passes.get("leave1", {})),
        ("KV", "ARRIVAL", "15:10", "3", passes.get("arrive2", {})),
        ("KV", "DEPARTURE", "15:11", "3", passes.get("leave2", {})),
        ("LR", "ARRIVAL", "15:40", "1", {}),
    ]
    return train(
        1,
        [
            timetable_row(code, kind, f"2026-10-04T{time}:00.000Z", **({"commercialTrack": track} if track else {}), **fields)
            for code, kind, time, track, fields in rows
        ],
        commuterLineID="R",
        **extra,
    )


def at(time: str) -> str:
    return f"2026-10-04T{time}:00.000Z"


# A train's row at the station is the first that hasn't come in or left and is inside its window, a minute for a
# departure and half an hour for an arrival, cancelled ones included. A cancelled row has never come in or left,
# whatever else it says. Without such a row an arrival is the last that came in, and a departure has none.
@pytest.mark.parametrize(
    ("case", "now", "direction", "passes", "extra", "expected"),
    [
        ("leave: the first leg cancelled, the second to come", "15:00", "departures", {"leave1": {"cancelled": True}}, {}, ("15:11", None)),
        (
            "leave: the first left, the second cancelled",
            "15:00",
            "departures",
            {"leave1": {"actualTime": at("14:21")}, "leave2": {"cancelled": True}},
            {},
            ("15:11", True),
        ),
        (
            "leave: cancelled, with an actual time all the same",
            "14:21",
            "departures",
            {"leave1": {"cancelled": True, "actualTime": at("14:21")}},
            {},
            ("14:21", True),
        ),
        ("leave: exactly a minute past", "14:22", "departures", {}, {}, ("14:21", None)),
        ("leave: both past, none", "15:20", "departures", {"leave1": {"cancelled": True}, "leave2": {"cancelled": True}}, {}, None),
        (
            "arrive: the first come in, the second cancelled",
            "14:30",
            "arrivals",
            {"arrive1": {"actualTime": at("14:20")}, "arrive2": {"cancelled": True}},
            {},
            ("15:10", True),
        ),
        (
            "arrive: cancelled whole, the first in its half hour by its estimate",
            "15:00",
            "arrivals",
            {"arrive1": {"cancelled": True, "liveEstimateTime": at("14:45")}, "arrive2": {"cancelled": True}},
            {"cancelled": True},
            ("14:20", True),
        ),
        (
            "arrive: cancelled whole, the second",
            "15:00",
            "arrivals",
            {"arrive1": {"cancelled": True}, "arrive2": {"cancelled": True}},
            {"cancelled": True},
            ("15:10", True),
        ),
        (
            "arrive: cancelled whole, both past",
            "15:45",
            "arrivals",
            {"arrive1": {"cancelled": True}, "arrive2": {"cancelled": True}},
            {"cancelled": True},
            None,
        ),
        (
            "arrive: cancelled, with an actual time all the same",
            "14:25",
            "arrivals",
            {"arrive1": {"cancelled": True, "actualTime": at("14:20")}, "arrive2": {"cancelled": True}},
            {},
            ("14:20", True),
        ),
        (
            "arrive: not come in, exactly half an hour past",
            "15:40",
            "arrivals",
            {"arrive1": {"actualTime": at("14:20")}},
            {},
            ("15:10", None),
        ),
        (
            "leave: cancelled whole, with an actual time all the same",
            "14:21",
            "departures",
            {"leave1": {"actualTime": at("14:21")}},
            {"cancelled": True},
            ("14:21", True),
        ),
    ],
)
def test_a_trains_row_is_its_first_still_current(
    case: str, now: str, direction: str, passes: dict, extra: dict, expected: tuple | None
) -> None:
    trains = [ring_passes(passes, **extra)]
    when = dt_util.parse_datetime(f"2026-10-04T{now}:00+00:00")
    config = StationDeparturesConfig.from_data({"station": "KV", "departures": 5, "direction": direction})
    if direction == "departures":
        found = build_departures(trains, config, NAMES, {}, load_texts("fi"), when)
    else:
        found = build_arrivals(trains, config, NAMES, {}, load_texts("fi"), when)
    got = (found[0]["scheduled"][11:16], found[0].get("cancelled")) if found else None
    assert got == expected, case
    assert not any(item.get("arrived") and item.get("cancelled") for item in found), "a cancelled one never comes in"


def leaving(number: int, time: str, cancelled: bool = False) -> dict:
    """A train from Lappeenranta to Helsinki leaving at `time` (15:05), cancelled or not."""
    extra = {"cancelled": True} if cancelled else {}
    return train(
        number,
        [
            timetable_row("LR", "DEPARTURE", f"2026-10-04T{time}:00.000Z", **extra),
            timetable_row("HKI", "ARRIVAL", "2026-10-04T18:00:00.000Z"),
        ],
    )


# The count is of the trains not cancelled. Cancelled ones before the last counted are listed too, in their place by
# time, so a run of cancellations never pushes the next train that runs off the list. Arrivals that are over, the latest
# two, are listed besides them as before.
@pytest.mark.parametrize(
    ("direction", "count", "trains", "expected"),
    [
        ("departures", 1, [(1, "15:05", True), (2, "15:10", False), (3, "15:20", False)], ["IC 1", "IC 2"]),
        ("departures", 2, [(1, "15:05", False), (2, "15:10", True), (3, "15:20", False), (4, "15:30", True)], ["IC 1", "IC 2", "IC 3"]),
        ("departures", 2, [(1, "15:05", True), (2, "15:10", True)], ["IC 1", "IC 2"]),
        ("departures", 1, [(1, "15:05", False), (2, "15:10", True)], ["IC 1"]),
        ("departures", 2, [(1, "15:05", False), (2, "15:10", True), (3, "15:20", True)], ["IC 1", "IC 2"]),
        ("departures", 2, [(n, f"15:{n:02d}", True) for n in range(1, 6)], ["IC 1", "IC 2"]),
        (
            "departures",
            3,
            [(1, "15:01", True), (2, "15:02", False), (3, "15:03", True), (4, "15:04", True), (5, "15:05", True)],
            ["IC 1", "IC 2", "IC 3"],
        ),
        ("arrivals", 1, [(1, "15:05", True), (2, "15:10", True), (3, "15:20", True)], ["IC 1"]),
        (
            "departures",
            2,
            [(1, "15:01", True), (2, "15:02", True), (3, "15:03", False), (4, "15:04", True), (5, "15:05", True)],
            ["IC 1", "IC 2", "IC 3"],
        ),
        (
            "arrivals",
            2,
            [(1, "15:01", True), (2, "15:02", True), (3, "15:03", False), (4, "15:04", True), (5, "15:05", True)],
            ["IC 1", "IC 2", "IC 3"],
        ),
        ("arrivals", 1, [(9, "14:50", True), (1, "15:05", True), (2, "15:10", True), (3, "15:20", True)], ["IC 9", "IC 1"]),
        ("departures", 2, [], []),
        ("arrivals", 2, [], []),
        ("arrivals", 1, [(1, "15:05", True), (2, "15:10", False), (3, "15:20", False)], ["IC 1", "IC 2"]),
        ("arrivals", 1, [(9, "14:50", True), (1, "15:00", True), (2, "15:10", False)], ["IC 9", "IC 1", "IC 2"]),
        ("arrivals", 2, [(1, "15:05", False), (2, "15:10", True), (3, "15:20", False), (4, "15:30", True)], ["IC 1", "IC 2", "IC 3"]),
    ],
)
def test_the_count_is_of_the_trains_not_cancelled(direction: str, count: int, trains: list, expected: list[str]) -> None:
    now = dt_util.parse_datetime("2026-10-04T15:00:00+00:00")
    config = StationDeparturesConfig.from_data({"station": "LR", "departures": count, "direction": direction})
    if direction == "departures":
        found = build_departures([leaving(*t) for t in trains], config, NAMES, {}, load_texts("fi"), now)
    else:
        built = [through(n, f"2026-10-04T{time}:00.000Z", **({"cancelled": True} if cancelled else {})) for n, time, cancelled in trains]
        found = build_arrivals(built, config, NAMES | {"JNS": "Joensuu"}, {}, load_texts("fi"), now)
    assert [item["line"] for item in found] == expected


def test_stops_at_filters_before_the_count_of_those_not_cancelled() -> None:
    def to(number: int, time: str, last: str, cancelled: bool = False) -> dict:
        extra = {"cancelled": True} if cancelled else {}
        rows = [
            timetable_row("LR", "DEPARTURE", f"2026-10-04T{time}:00.000Z", **extra),
            timetable_row(last, "ARRIVAL", "2026-10-04T18:00:00.000Z"),
        ]
        return train(number, rows)

    trains = [to(1, "15:05", "HKI", cancelled=True), to(2, "15:10", "KV"), to(3, "15:20", "HKI"), to(4, "15:30", "HKI")]
    config = StationDeparturesConfig.from_data({"station": "LR", "stops_at": "HKI", "departures": 1})
    now = dt_util.parse_datetime("2026-10-04T15:00:00+00:00")
    assert [d["line"] for d in build_departures(trains, config, NAMES, {}, load_texts("fi"), now)] == ["IC 1", "IC 3"]


def test_a_ring_train_cancelled_whole_arrives_by_the_pass_not_yet_past() -> None:
    [found] = arrivals([ring(1, {"cancelled": True}, {"cancelled": True}) | {"cancelled": True}], station="KV")
    assert (found["scheduled"][11:16], found.get("cancelled"), found.get("arrived")) == ("15:10", True, None)


# The count is of the arrivals still to come. Those that have come in are listed besides them, and don't take its places.
@pytest.mark.parametrize(
    ("count", "came_in", "expected"),
    [
        (1, 1, ["IC 1", "IC 5"]),
        (1, 3, ["IC 2", "IC 3", "IC 5"]),
        (2, 2, ["IC 1", "IC 2", "IC 5", "IC 6"]),
        (3, 0, ["IC 5", "IC 6", "IC 7"]),
        (5, 3, ["IC 2", "IC 3", "IC 5", "IC 6", "IC 7"]),
    ],
)
def test_the_count_is_of_the_arrivals_still_to_come(count: int, came_in: int, expected: list[str]) -> None:
    times = ("14:40", "14:45", "14:50")[:came_in]
    trains = [through(n, f"2026-10-04T{t}:00.000Z", actualTime=f"2026-10-04T{t}:00.000Z") for n, t in enumerate(times, 1)]
    trains += [through(n, f"2026-10-04T15:{m}:00.000Z") for n, m in ((5, 10), (6, 20), (7, 30))]
    assert [found["line"] for found in arrivals(trains, count=count)] == expected


def test_a_cancelled_arrival_past_its_time_is_over_and_listed_besides_the_count_but_never_comes_in() -> None:
    came_in = [
        through(n, f"2026-10-04T14:{m}:00.000Z", actualTime=f"2026-10-04T14:{m}:00.000Z") for n, m in ((1, 35), (2, 40), (3, 45), (4, 50))
    ]
    coming = [through(n, f"2026-10-04T15:{m}:00.000Z") for n, m in ((5, 10), (6, 20), (7, 30))]
    cancelled = through(8, "2026-10-04T14:55:00.000Z", cancelled=True, actualTime="2026-10-04T14:55:00.000Z")
    found = arrivals([*came_in, cancelled, *coming], count=3)
    assert [arrival["line"] for arrival in found] == ["IC 4", "IC 8", "IC 5", "IC 6", "IC 7"], "the latest two over, and three to come"
    assert found[1] == arrival(
        id="train-arrival:2026-10-04/8",
        line="IC 8",
        scheduled="2026-10-04T14:55:00+00:00",
        estimated="2026-10-04T14:55:00+00:00",
        realtime=False,
        cancelled=True,
    )


def test_a_train_through_the_station_arrives_and_leaves_under_two_ids() -> None:
    trains = [through(1, "2026-10-04T15:20:00.000Z")]
    config = StationDeparturesConfig.from_data({"station": "LR", "departures": 5, "direction": "both"})
    [leaving] = build_departures(trains, config, NAMES | {"JNS": "Joensuu"}, {}, load_texts("fi"), DEPARTURES_NOW)
    [coming] = arrivals(trains)
    assert (leaving["headsign"], coming["headsign"]) == ("Joensuu", "Helsinki")
    assert leaving["id"] != coming["id"]


def test_the_next_arrival_is_the_first_neither_cancelled_nor_come_in() -> None:
    trains = [
        {"line": "IC 1", "estimated": "14:50", "arrived": True},
        {"line": "IC 2", "estimated": "15:05", "cancelled": True},
        {"line": "IC 3", "estimated": "15:20"},
    ]
    station = StationDepartures("LR", "Lappeenranta", {"arrivals": trains}, [])
    assert station.next_train("arrivals")["line"] == "IC 3"
