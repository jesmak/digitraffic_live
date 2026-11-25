"""Ports: a port's winter navigation restrictions and suspensions, and the ships calling at it, in the departures format.

The restrictions and suspensions are winter navigation's (`winter-navigation/v2/locations`), every port's in one
request. The calls are the port call service's (`port-call/v1/port-calls`), with every time in them set by the ship's
agent, the port or the pilot weeks ahead, so they are announcements rather than live estimates, until the actual time
of arrival or departure comes in. The format is documented in departures-card (docs/departures-format.md).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util
from homeassistant.util.json import json_loads

from .const import CALLS_FILED_UNDER, CONF_DEPARTURES, CONF_PORT, CONF_PORT_CALLS, CONF_WINTER_LOCATION, DEFAULT_DEPARTURES
from .station_departures import ARRIVAL_PAST, ARRIVED_LISTED, DEPARTURE_PAST, counted, is_over

# The calls asked for: from half a day back, so a ship hours behind its announced time is still found once it comes in,
# to a week ahead, as a small port has only a few calls a day.
CALLS_BEHIND = timedelta(hours=12)
CALLS_AHEAD = timedelta(days=7)

# The port call service's vessel type codes (`port-call/v1/code-descriptions`) of the ships that carry passengers: a
# passenger vessel, a passenger car ferry and a rail ferry. Every other is a ship.
FERRY_TYPES = frozenset({10, 20, 30})
# The port areas that are no harbour, at anchor and unknown. Every port has them, so they don't tell whose a call is.
SHARED_AREAS = frozenset({"ANK", "MUU"})
# Berths and port areas with no name of their own.
UNKNOWN_PLACES = frozenset({"", "MUU", "unknow", "Ei tiedossa"})
# Winter navigation's reasons for a suspension, as the attribute's states.
SUSPENSION_REASONS = {"CLOSED_DUE_BAD_WEATHER": "bad_weather", "CLOSED_DUE_CREW_CHANGE": "crew_change"}


@dataclass(frozen=True)
class PortConfig:
    port: str
    winter_location: str | None
    ships: bool
    count: int

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> PortConfig:
        """From config subentry data."""
        return cls(
            port=str(data[CONF_PORT]),
            winter_location=str(data[CONF_PORT]) if data.get(CONF_WINTER_LOCATION) else None,
            ships=bool(data.get(CONF_PORT_CALLS)),
            count=int(data.get(CONF_DEPARTURES, DEFAULT_DEPARTURES)),
        )

    @property
    def calls_locode(self) -> str:
        """The UN/LOCODE the port's calls are filed under."""
        return CALLS_FILED_UNDER.get(self.port, self.port)

    @property
    def shares_calls(self) -> bool:
        """Whether the port's calls are filed together with another port's, so its harbours tell them apart."""
        return self.port in CALLS_FILED_UNDER or self.port in CALLS_FILED_UNDER.values()


@dataclass(frozen=True)
class PortIndex:
    """Every location's name by UN/LOCODE, and the port area codes of each Finnish port that has calls."""

    names: dict[str, str]
    harbours: dict[str, frozenset[str]]


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime | None  # None when open-ended
    text: str  # a restriction's text, or a suspension's reason
    closed: bool = False  # whether a suspension closes the port to every operation

    def covers(self, now: datetime) -> bool:
        return self.start <= now and (self.end is None or now < self.end)

    def as_attribute(self, key: str) -> dict[str, Any]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat() if self.end else None, key: self.text}


def in_force(periods: Sequence[Period], now: datetime) -> Period | None:
    return next((period for period in periods if period.covers(now)), None)


@dataclass(frozen=True)
class WinterLocation:
    """A port's periods in order, the whole winter's, as winter navigation keeps them until the next."""

    name: str
    restrictions: list[Period]
    suspensions: list[Period]


def port_index(raw: bytes) -> PortIndex:
    """The port call service's locations and port areas (about five megabytes), parsed in the executor."""
    data = json_loads(raw)
    if not isinstance(data, dict):
        raise ValueError("The port list isn't an object")
    names = {
        str(feature["locode"]): str(feature["properties"]["locationName"])
        for feature in (data.get("ssnLocations") or {}).get("features") or []
        if feature.get("locode") and (feature.get("properties") or {}).get("locationName")
    }
    harbours: dict[str, set[str]] = {}
    for feature in (data.get("portAreas") or {}).get("features") or []:
        if feature.get("locode"):
            harbours.setdefault(str(feature["locode"]), set()).add(str(feature.get("portAreaCode") or ""))
    return PortIndex(names, {locode: frozenset(codes) for locode, codes in harbours.items()})


def winter_locations(data: Mapping[str, Any]) -> dict[str, WinterLocation]:
    """Winter navigation's ports by UN/LOCODE. A location has a comma-separated list of them, and fairways have none."""
    locations: dict[str, WinterLocation] = {}
    for feature in data.get("features") or []:
        properties = feature.get("properties") or {}
        locodes = [locode.strip() for locode in str(properties.get("locodeList") or "").split(",") if locode.strip()]
        if not locodes:
            continue
        location = WinterLocation(
            name=str(properties.get("name") or locodes[0]),
            restrictions=sorted(
                (
                    period
                    for item in properties.get("restrictions") or []
                    if (period := _period(item, str(item.get("textCompilation") or "")))
                ),
                key=lambda period: period.start,
            ),
            suspensions=sorted(
                (
                    period
                    for item in properties.get("suspensions") or []
                    if (period := _period(item, suspension_reason(item.get("dueTo")), bool(item.get("portsClosed"))))
                ),
                key=lambda period: period.start,
            ),
        )
        for locode in locodes:
            locations[locode] = location
    return locations


def _period(item: Mapping[str, Any], text: str, closed: bool = False) -> Period | None:
    start = dt_util.parse_datetime(str(item.get("startTime") or ""))
    if start is None:
        return None
    return Period(start, dt_util.parse_datetime(str(item.get("endTime") or "")), text, closed)


def suspension_reason(due_to: Any) -> str:
    """bad_weather or crew_change; a reason not seen before as Digitraffic writes it, in lower case."""
    code = str(due_to or "")
    return SUSPENSION_REASONS.get(code, code.removeprefix("CLOSED_DUE_").lower())


def is_ports_own(call: Mapping[str, Any], port: str, harbours: Mapping[str, frozenset[str]]) -> bool:
    """Whether a call filed under the port's UN/LOCODE is at the port itself. A port filed under another's has the calls
    at its own port areas, and the other has the rest. A call at anchor or at an unknown area is both ports'."""
    codes = {str(area.get("portAreaCode") or "") for area in call.get("portAreaDetails") or []}
    if port in CALLS_FILED_UNDER:
        return bool(codes & harbours.get(port, frozenset()))
    guests = (harbours.get(guest, frozenset()) for guest, host in CALLS_FILED_UNDER.items() if host == port)
    return not codes <= frozenset().union(*guests) - SHARED_AREAS


def build_port_calls(raw: bytes, config: PortConfig, index: PortIndex, arrivals: bool, now: datetime) -> list[dict[str, Any]]:
    """The arrivals or departures at the port from its calls (parsed in the executor), in order of their time, as the
    station departures are: until a minute past a departure, and the configured count of arrivals still to come, with
    the latest two that have come in within half an hour besides them."""
    data = json_loads(raw)
    calls = data.get("portCalls") if isinstance(data, dict) else None
    if not isinstance(calls, list):
        raise ValueError("The port calls aren't a list")
    build = build_arrival if arrivals else build_departure
    rows = sorted(
        (
            row
            for call in calls
            if is_ports_own(call, config.port, index.harbours) and (row := build(call, config, index.names)) is not None
        ),
        key=lambda row: row["estimated"],
    )
    if not arrivals:
        return counted([row for row in rows if dt_util.parse_datetime(row["estimated"]) >= now - DEPARTURE_PAST], config.count)
    rows = [row for row in rows if dt_util.parse_datetime(row["estimated"]) >= now - ARRIVAL_PAST]
    over = [row for row in rows if is_over(row, now)]
    coming = [row for row in rows if not is_over(row, now)]
    return sorted(over[-ARRIVED_LISTED:] + counted(coming, config.count), key=lambda row: row["estimated"])


def build_arrival(call: Mapping[str, Any], config: PortConfig, names: Mapping[str, str]) -> dict[str, Any] | None:
    """A ship's arrival at its first port area, from the port it comes from. None without an announced time."""
    areas = call.get("portAreaDetails") or []
    return _row(call, areas[0], "eta", "ata", call.get("prevPort"), config, names) if areas else None


def build_departure(call: Mapping[str, Any], config: PortConfig, names: Mapping[str, str]) -> dict[str, Any] | None:
    """A ship's departure from its last port area, to the port it goes to next. None without an announced time."""
    areas = call.get("portAreaDetails") or []
    return _row(call, areas[-1], "etd", "atd", call.get("nextPort"), config, names) if areas else None


def _row(
    call: Mapping[str, Any],
    area: Mapping[str, Any],
    announced_key: str,
    actual_key: str,
    other_port: Any,
    config: PortConfig,
    names: Mapping[str, str],
) -> dict[str, Any] | None:
    announced = dt_util.parse_datetime(str(area.get(announced_key) or ""))
    if announced is None:
        return None
    actual = dt_util.parse_datetime(str(area.get(actual_key) or ""))
    arrival = announced_key == "eta"
    vessel = str(call.get("vesselName") or "").strip()
    # Calls name the port itself as where a ship comes from or goes next, as seen at Kotka and Helsinki.
    port = str(other_port or "")
    place = names.get(port, port) if port and port not in (config.port, config.calls_locode) else ""
    berth = str(area.get("berthCode") or "").strip()
    harbour = str(area.get("portAreaName") or "").strip()
    row: dict[str, Any] = {
        "id": f"{'call-arrival' if arrival else 'call'}:{call.get('portCallId')}",
        "line": "",
        "mode": "ferry" if call.get("vesselTypeCode") in FERRY_TYPES else "ship",
        "headsign": " · ".join(part for part in (vessel, place) if part),
        "scheduled": announced.isoformat(),
        "estimated": (actual or announced).isoformat(),
        "realtime": actual is not None,
        "delay": int((actual - announced).total_seconds()) if actual is not None else 0,
        "platform": berth if berth not in UNKNOWN_PLACES else None,
        "harbour": harbour if harbour not in UNKNOWN_PLACES else None,
        "arrived": (arrival and actual is not None) or None,
    }
    return {key: value for key, value in row.items() if value is not None}
