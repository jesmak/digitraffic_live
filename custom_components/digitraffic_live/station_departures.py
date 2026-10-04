"""Station departures: the next passenger trains to leave one railway station, in the departures format.

The format is documented in departures-card (docs/departures-format.md), which shows these sensors.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.util import dt as dt_util

from .const import CONF_DEPARTURES, CONF_STATION, CONF_STOPS_AT, DEFAULT_DEPARTURES
from .texts import Texts
from .trains import notice_key, station_name

# Only trains people can board: no cargo, locomotives, test drives or work trains.
PASSENGER_CATEGORIES = ("Long-distance", "Commuter")

# Trains between two stations can't be limited to passenger trains in the request, so a few more are fetched for the
# cargo and work trains that are left out afterwards.
BETWEEN_FETCH_FACTOR = 2


@dataclass(frozen=True)
class StationDeparturesConfig:
    station: str  # station short code
    stops_at: str | None  # only trains that stop here later
    count: int

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> StationDeparturesConfig:
        """From config subentry data."""
        return cls(
            station=str(data[CONF_STATION]),
            stops_at=data.get(CONF_STOPS_AT) or None,
            count=int(data.get(CONF_DEPARTURES, DEFAULT_DEPARTURES)),
        )

    @property
    def fetch_count(self) -> int:
        return self.count * BETWEEN_FETCH_FACTOR if self.stops_at else self.count


def build_departures(
    trains: Sequence[Mapping[str, Any]],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
) -> list[dict[str, Any]]:
    """The departures from the station in order of their estimated time, limited to the configured count."""
    departures = [
        departure
        for train in trains
        if train.get("trainCategory") in PASSENGER_CATEGORIES
        and (departure := build_departure(train, config, station_names, train_notices, texts)) is not None
    ]
    departures.sort(key=lambda departure: departure["estimated"])
    return departures[: config.count]


def build_departure(
    train: Mapping[str, Any],
    config: StationDeparturesConfig,
    station_names: Mapping[str, str],
    train_notices: Mapping[str, list[str]],
    texts: Texts,
) -> dict[str, Any] | None:
    """One train's departure from the station.

    None when the train doesn't leave from the station, has already left, or doesn't stop at `stops_at` later.
    """
    rows = train.get("timeTableRows") or []
    index = next(
        (
            index
            for index, row in enumerate(rows)
            if row.get("stationShortCode") == config.station
            and row.get("type") == "DEPARTURE"
            and row.get("commercialStop")
            and not row.get("actualTime")
        ),
        None,
    )
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
        "line": train.get("commuterLineID")
        or f"{train.get('trainType') or ''} {train.get('trainNumber') or ''}".strip(),
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
