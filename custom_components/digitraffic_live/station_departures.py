"""Station departures and arrivals: the next passenger trains to leave or reach one railway station, in the departures
format.

The format is documented in departures-card (docs/departures-format.md), which shows these sensors.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from .const import CONF_DEPARTURES, CONF_DIRECTION, CONF_STATION, CONF_STOPS_AT, DEFAULT_DEPARTURES, DIRECTION_DEPARTURES, DIRECTION_SENSORS
from .texts import Texts
from .trains import notice_key, station_name

# Only trains people can board: no cargo, locomotives, test drives or work trains.
PASSENGER_CATEGORIES = ("Long-distance", "Commuter")

# Twice the count is fetched. Trains between two stations can't be limited to passenger trains in the request, and
# Digitraffic keeps a train that hasn't left or come in, a cancelled one among them, for up to an hour past its time, so
# some of the answer is left out afterwards.
FETCH_FACTOR = 2
# A departure is listed until a minute past its time, as departures-card shows it.
DEPARTURE_PAST = timedelta(minutes=1)

# An arrival stays half an hour past its time, which once it has come in is its actual time, for meeting someone off it,
# as departures-card shows it. Of those that are over (see is_over), only the latest two are listed, besides the count.
ARRIVAL_PAST = timedelta(minutes=30)
ARRIVED_LISTED = 2


@dataclass(frozen=True)
class StationDeparturesConfig:
    station: str  # station short code
    stops_at: str | None  # only trains that stop here later; departures only
    count: int
    # departures, arrivals or both. A subentry from before arrivals has none, and is departures.
    direction: str = DIRECTION_DEPARTURES

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> StationDeparturesConfig:
        """From config subentry data."""
        return cls(
            station=str(data[CONF_STATION]),
            stops_at=data.get(CONF_STOPS_AT) or None,
            count=int(data.get(CONF_DEPARTURES, DEFAULT_DEPARTURES)),
            direction=str(data.get(CONF_DIRECTION, DIRECTION_DEPARTURES)),
        )

    @property
    def directions(self) -> list[str]:
        """The sensors the station has, "departures" and "arrivals"."""
        return DIRECTION_SENSORS[self.direction]

    @property
    def fetch_count(self) -> int:
        return self.count * FETCH_FACTOR


def build_departures(
    trains: Sequence[Mapping[str, Any]],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
    now: datetime,
) -> list[dict[str, Any]]:
    """The departures from the station in order of their estimated time, until a minute past it, the configured count of
    those not cancelled (see counted)."""
    departures = [
        departure
        for train in trains
        if train.get("trainCategory") in PASSENGER_CATEGORIES
        and (departure := build_departure(train, config, station_names, train_notices, texts, now)) is not None
    ]
    departures.sort(key=lambda departure: departure["estimated"])
    return counted(departures, config.count)


def build_departure(
    train: Mapping[str, Any],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
    now: datetime,
) -> dict[str, Any] | None:
    """One train's departure from the station, by its row still current (see current_row).

    None when the train doesn't leave from the station, has left or is a minute past, or doesn't stop at `stops_at` later.
    """
    rows = train.get("timeTableRows") or []
    index = current_row(train, rows, config.station, "DEPARTURE", now, DEPARTURE_PAST)
    if index is None:
        return None
    if config.stops_at and not any(
        row.get("stationShortCode") == config.stops_at and row.get("type") == "ARRIVAL" and row.get("commercialStop")
        for row in rows[index + 1 :]
    ):
        return None

    row = rows[index]
    scheduled = dt_util.parse_datetime(row.get("scheduledTime") or "")
    if scheduled is None:
        return None
    estimate = dt_util.parse_datetime(row.get("liveEstimateTime") or "")
    destination = str(rows[-1].get("stationShortCode") or "")
    cancelled = bool(train.get("cancelled") or row.get("cancelled"))
    track = str(row.get("commercialTrack") or "").lstrip("0")
    # From the times themselves: differenceInMinutes is rounded, and would disagree with the clock times shown.
    delay = int((estimate - scheduled).total_seconds()) if estimate is not None else 0

    departure: dict[str, Any] = {
        "id": f"train:{train.get('departureDate')}/{train.get('trainNumber')}",
        "line": train.get("commuterLineID") or f"{train.get('trainType') or ''} {train.get('trainNumber') or ''}".strip(),
        "mode": "train",
        "headsign": station_names.get(destination) or destination,
        "scheduled": scheduled.isoformat(),
        "estimated": (estimate or scheduled).isoformat(),
        "realtime": estimate is not None,
        "delay": delay,
        "platform": track or None,
        "cancelled": cancelled or None,
        "notice": departure_notice(train, rows, index, cancelled, delay, train_notices, texts),
    }
    return {key: value for key, value in departure.items() if value is not None}


def build_arrivals(
    trains: Sequence[Mapping[str, Any]],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
    now: datetime,
) -> list[dict[str, Any]]:
    """The configured count of arrivals still to come and not cancelled (see counted), and besides them the latest two that
    are over (see is_over) within half an hour, in order of their estimated time, so neither cancellations nor those that
    are over push the next arrival off the list."""
    arrivals = [
        arrival
        for train in trains
        if train.get("trainCategory") in PASSENGER_CATEGORIES
        and (arrival := build_arrival(train, config, station_names, train_notices, texts, now)) is not None
        and dt_util.parse_datetime(arrival["estimated"]) >= now - ARRIVAL_PAST
    ]
    arrivals.sort(key=lambda arrival: arrival["estimated"])
    over = [arrival for arrival in arrivals if is_over(arrival, now)]
    coming = [arrival for arrival in arrivals if not is_over(arrival, now)]
    return sorted(over[-ARRIVED_LISTED:] + counted(coming, config.count), key=lambda arrival: arrival["estimated"])


def counted(trains: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    """The first `count` trains not cancelled, in order, with the cancelled ones among them, so a run of cancellations
    never pushes the next train that runs off the list. When fewer than `count` aren't cancelled, as in a strike, the cancelled
    ones after the last of them fill the list up to `count`."""
    last, counting = -1, 0
    for index, item in enumerate(trains):
        if counting >= count:
            break
        if not item.get("cancelled"):
            last, counting = index, counting + 1
    listed = trains[: last + 1]
    if counting >= count:
        return listed
    return listed + trains[last + 1 :][: max(count - len(listed), 0)]


def is_over(arrival: Mapping[str, Any], now: datetime) -> bool:
    """An arrival that has come in, or one cancelled and past its time: listed besides the count, the latest two."""
    return bool(arrival.get("arrived") or (arrival.get("cancelled") and dt_util.parse_datetime(arrival["estimated"]) < now))


def build_arrival(
    train: Mapping[str, Any],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
    now: datetime,
) -> dict[str, Any] | None:
    """One train's arrival at the station, by its row still current (see current_row), from where it set off. None when it
    has no row at the station still current or come in. One that has come in is `arrived`, and its actual time is its
    estimated time. A ring train back where it started, as the I and P trains at Helsinki, arrives from there.
    """
    rows = train.get("timeTableRows") or []
    index = current_row(train, rows, config.station, "ARRIVAL", now, ARRIVAL_PAST)
    if index is None:
        return None
    origin = str(rows[0].get("stationShortCode") or "")
    row = rows[index]
    scheduled = dt_util.parse_datetime(row.get("scheduledTime") or "")
    if scheduled is None:
        return None
    cancelled = bool(train.get("cancelled") or row.get("cancelled"))
    actual = None if cancelled else dt_util.parse_datetime(row.get("actualTime") or "")
    estimate = actual or dt_util.parse_datetime(row.get("liveEstimateTime") or "")
    track = str(row.get("commercialTrack") or "").lstrip("0")
    delay = int((estimate - scheduled).total_seconds()) if estimate is not None else 0

    arrival: dict[str, Any] = {
        # A train through the station has the same number arriving and leaving, so arrivals have ids of their own.
        "id": f"train-arrival:{train.get('departureDate')}/{train.get('trainNumber')}",
        "line": train.get("commuterLineID") or f"{train.get('trainType') or ''} {train.get('trainNumber') or ''}".strip(),
        "mode": "train",
        "headsign": station_names.get(origin) or origin,
        "scheduled": scheduled.isoformat(),
        "estimated": (estimate or scheduled).isoformat(),
        "realtime": estimate is not None,
        "delay": delay,
        "platform": track or None,
        "cancelled": cancelled or None,
        "arrived": (actual is not None and not cancelled) or None,
        "notice": departure_notice(train, rows, index, cancelled, delay, train_notices, texts),
    }
    return {key: value for key, value in arrival.items() if value is not None}


def current_row(
    train: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], station: str, kind: str, now: datetime, window: timedelta
) -> int | None:
    """The index of a train's row at the station still current: the first of its kind, ARRIVAL or DEPARTURE, with a
    commercial stop, that hasn't come in or left and is inside `window` past its time, cancelled ones included. A train
    through the station twice, as the I and P trains pass Pasila, has two. A cancelled row has never come in or left,
    whatever else it says. Without such a row an arrival is the last that came in, and a departure has none."""

    def done(row: Mapping[str, Any]) -> bool:
        return bool(row.get("actualTime")) and not (train.get("cancelled") or row.get("cancelled"))

    passes = [
        index
        for index, row in enumerate(rows)
        if row.get("stationShortCode") == station and row.get("type") == kind and row.get("commercialStop")
    ]
    current = next((index for index in passes if not done(rows[index]) and pass_time(rows[index]) >= now - window), None)
    if current is not None:
        return current
    finished = [index for index in passes if done(rows[index])] if kind == "ARRIVAL" else []
    return finished[-1] if finished else None


def pass_time(row: Mapping[str, Any]) -> datetime:
    """A timetable row's live estimate, or else its timetable time; the earliest time when it has neither."""
    return dt_util.parse_datetime(row.get("liveEstimateTime") or row.get("scheduledTime") or "") or datetime.min.replace(tzinfo=dt_util.UTC)


def departure_notice(
    train: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    index: int,
    cancelled: bool,
    delay: int,
    train_notices: Mapping[str, list[str]],
    texts: Texts,
) -> str | None:
    """The train's own passenger notice, which says what to do ("Passengers are directed to train S106"), or else why
    it is cancelled or late. A cause stays on the row after the train has caught up, so it's told only while it matters.
    """
    if notices := train_notices.get(notice_key(train.get("trainNumber"), train.get("departureDate"))):
        return " ".join(notices)
    return cause_text(rows, index, cancelled, texts) if cancelled or delay >= 60 else None


def cause_text(rows: Sequence[Mapping[str, Any]], index: int, cancelled: bool, texts: Texts) -> str | None:
    """Why the train is late or cancelled, as one short phrase: the cause's top-level category, in our own words.

    Digitraffic's cause names are in Finnish only and written for the railway, so each category has a text of its
    own. The latest cause recorded on the way to the station explains a delay; a cancelled train may have its cause
    anywhere on the route.
    """
    causes = [cause for row in rows[: index + 1] for cause in row.get("causes") or []]
    if not causes and cancelled:
        causes = [cause for row in rows for cause in row.get("causes") or []][:1]
    if not causes:
        return None
    key = f"cause_{causes[-1].get('categoryCode')}"
    return texts(key) if texts.has(key) else texts("cause_I")


def station_name_index(stations: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Station names by short code, without the "asema" the list adds to some: "Helsinki asema" → "Helsinki"."""
    return {
        str(station["stationShortCode"]): station_name(station.get("stationName"))
        for station in stations
        if station.get("stationShortCode")
    }
