"""Ships: AIS positions and vessel register data as map feed features.

Field meanings follow ITU-R M.1371 and the Digitraffic marine API
(https://meri.digitraffic.fi/swagger/).
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .api import DigitrafficClient, DigitrafficError, DigitrafficNotFound
from .const import (
    CONF_AREA,
    CONF_ICEBREAKERS,
    CONF_INCLUDE_MOORED,
    CONF_MAX_AGE_MINUTES,
    CONF_SHIP_TYPES,
    DEFAULT_SHIP_MAX_AGE_MINUTES,
)
from .feed import iso_from_epoch_ms, point_feature, row
from .geo import Area
from .texts import Texts

_LOGGER = logging.getLogger(__name__)

# Ship types for the ship_types setting. Each is also a feed kind ("ship.cargo") and a text key ("ship_cargo").
SHIP_TYPES = ("cargo", "tanker", "passenger", "pilot", "tug", "fishing", "pleasure", "other")

# AIS "not available" values.
AIS_SPEED_NOT_AVAILABLE = 102.3
AIS_COURSE_NOT_AVAILABLE = 360
AIS_DRAUGHT_NOT_AVAILABLE = 255

# Below this speed a ship has no meaningful direction and is drawn as a dot.
MOVING_SPEED_KNOTS = 0.5
KNOTS_TO_KMH = 1.852

NAV_STATUS_AT_ANCHOR = 1
NAV_STATUS_MOORED = 5

# Winter navigation activities only icebreakers do (see the winter navigation API documentation).
ICEBREAKER_ACTIVITIES = frozenset({"LOC", "MOVE", "TRANS"})

# For larger areas, one request for all of Finland is cheaper than a radius query.
FULL_FETCH_RADIUS_KM = 250


@dataclass(frozen=True)
class ShipFeedConfig:
    area: Area
    max_age_minutes: int
    ship_types: frozenset[str] | None  # None = all types
    include_moored: bool
    icebreakers: bool

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> ShipFeedConfig:
        """From config subentry data."""
        ship_types = frozenset(data.get(CONF_SHIP_TYPES) or ()) & frozenset(SHIP_TYPES)
        return cls(
            area=Area.from_selector(data[CONF_AREA]),
            max_age_minutes=int(data.get(CONF_MAX_AGE_MINUTES, DEFAULT_SHIP_MAX_AGE_MINUTES)),
            ship_types=ship_types or None,
            include_moored=bool(data.get(CONF_INCLUDE_MOORED, True)),
            icebreakers=bool(data.get(CONF_ICEBREAKERS, False)),
        )


# ---------------- interpreting AIS data ----------------


def ship_type(code: Any) -> str:
    """Maps an AIS ship type code to one of SHIP_TYPES."""
    try:
        value = int(code)
    except (TypeError, ValueError):
        return "other"
    if value == 30:
        return "fishing"
    if value in (31, 32, 52):
        return "tug"
    if value in (36, 37):
        return "pleasure"
    if value == 50:
        return "pilot"
    if 60 <= value <= 69:
        return "passenger"
    if 70 <= value <= 79:
        return "cargo"
    if 80 <= value <= 89:
        return "tanker"
    return "other"


def is_moored(nav_stat: Any) -> bool:
    return nav_stat in (NAV_STATUS_AT_ANCHOR, NAV_STATUS_MOORED)


def ship_heading(props: Mapping[str, Any]) -> float | None:
    """Where the ship points: true heading if known, otherwise course over ground, otherwise None.

    Course over ground is used only while the ship moves: a ship standing still
    reports a course (often 0) that means nothing.
    """
    heading = props.get("heading")
    if isinstance(heading, int) and 0 <= heading < 360:
        return heading
    course = props.get("cog")
    speed = speed_knots(props)
    if (
        isinstance(course, (int, float))
        and 0 <= course < AIS_COURSE_NOT_AVAILABLE
        and speed is not None
        and speed >= MOVING_SPEED_KNOTS
    ):
        return course
    return None


def speed_knots(props: Mapping[str, Any]) -> float | None:
    speed = props.get("sog")
    if isinstance(speed, (int, float)) and 0 <= speed < AIS_SPEED_NOT_AVAILABLE:
        return float(speed)
    return None


def is_stationary(props: Mapping[str, Any]) -> bool:
    """Moored, too slow to have a direction, or without speed or direction data."""
    speed = speed_knots(props)
    return is_moored(props.get("navStat")) or speed is None or speed < MOVING_SPEED_KNOTS or ship_heading(props) is None


def navigation_status_key(nav_stat: int) -> str:
    """Text key for an AIS navigational status. Codes 9–13 are reserved in the standard."""
    if 9 <= nav_stat <= 13:
        return "nav_reserved"
    if 0 <= nav_stat <= 8 or nav_stat == 14:
        return f"nav_{nav_stat}"
    return "nav_15"


def icebreaker_mmsis(data: Mapping[str, Any] | None) -> set[int]:
    """MMSI numbers of icebreakers in winter navigation data.

    Vessels typed as icebreakers, and (in case the type is missing) vessels that
    assist others, do icebreaker-only activities or are named as assisting.
    """
    result: set[int] = set()
    for vessel in (data or {}).get("vessels") or []:
        mmsi = vessel.get("mmsi")
        if mmsi and str(vessel.get("type") or "").lower() == "icebreaker":
            result.add(int(mmsi))
        for entry in [*(vessel.get("activities") or []), *(vessel.get("plannedAssistances") or [])]:
            assisting = (entry.get("assistingVessel") or {}).get("mmsi")
            if assisting:
                result.add(int(assisting))
            if mmsi and ("assistedVessel" in entry or entry.get("type") in ICEBREAKER_ACTIVITIES):
                result.add(int(mmsi))
    return result


# ---------------- vessel register ----------------


class VesselRegister:
    """Ship names and details from the AIS vessel register.

    Positions change every minute but register data rarely does, so each ship is
    looked up once and reused. When many ships are unknown at once (the first
    update of a large area), the whole register is downloaded instead.
    Shared by every ship feed.
    """

    def __init__(self, ttl_seconds: float = 6 * 3600, bulk_threshold: int = 40, concurrency: int = 4) -> None:
        self._ttl = ttl_seconds
        self._bulk_threshold = bulk_threshold
        self._concurrency = concurrency
        # mmsi → (register data, or None when the register doesn't know the ship; fetch time)
        self._entries: dict[int, tuple[dict[str, Any] | None, float]] = {}
        self._bulk_loaded_at: float | None = None
        self._lock = asyncio.Lock()

    def get(self, mmsi: int) -> dict[str, Any] | None:
        entry = self._entries.get(mmsi)
        return entry[0] if entry else None

    async def ensure(self, client: DigitrafficClient, mmsis: Iterable[int]) -> None:
        """Makes sure register data is cached for the given ships."""
        async with self._lock:
            now = time.monotonic()
            missing = sorted({mmsi for mmsi in mmsis if self._is_stale(mmsi, now)})
            if not missing:
                return

            bulk_is_old = self._bulk_loaded_at is None or now - self._bulk_loaded_at > self._ttl
            if len(missing) > self._bulk_threshold and bulk_is_old:
                await self._load_all(client, missing)
                return

            semaphore = asyncio.Semaphore(self._concurrency)

            async def load(mmsi: int) -> None:
                async with semaphore:
                    try:
                        data: dict[str, Any] | None = await client.vessel(mmsi)
                    except DigitrafficNotFound:
                        data = None
                    except DigitrafficError as err:
                        # Leave it uncached so the next update tries again.
                        _LOGGER.debug("Vessel %s lookup failed: %s", mmsi, err)
                        return
                    self._entries[mmsi] = (data, time.monotonic())

            await asyncio.gather(*(load(mmsi) for mmsi in missing))

    def _is_stale(self, mmsi: int, now: float) -> bool:
        entry = self._entries.get(mmsi)
        return entry is None or now - entry[1] > self._ttl

    async def _load_all(self, client: DigitrafficClient, missing: list[int]) -> None:
        try:
            vessels = await client.vessels()
        except DigitrafficError as err:
            _LOGGER.debug("Vessel register download failed: %s", err)
            return
        loaded_at = time.monotonic()
        self._bulk_loaded_at = loaded_at
        for vessel in vessels if isinstance(vessels, list) else []:
            if vessel.get("mmsi"):
                self._entries[int(vessel["mmsi"])] = (vessel, loaded_at)
        for mmsi in missing:
            self._entries.setdefault(mmsi, (None, loaded_at))


# ---------------- building the feed ----------------


async def fetch_ship_positions(client: DigitrafficClient, config: ShipFeedConfig, now_ms: int) -> list[dict[str, Any]]:
    """Recent AIS positions inside the area."""
    cutoff_ms = now_ms - config.max_age_minutes * 60_000
    area = config.area
    if area.radius_km <= FULL_FETCH_RADIUS_KM:
        data = await client.ais_locations(cutoff_ms, area.latitude, area.longitude, math.ceil(area.radius_km))
    else:
        data = await client.ais_locations(cutoff_ms)

    positions = []
    for feature in data.get("features") or []:
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        props = feature.get("properties") or {}
        if len(coordinates) < 2 or not props.get("mmsi"):
            continue
        received_ms = props.get("timestampExternal")
        if isinstance(received_ms, (int, float)) and received_ms < cutoff_ms:
            continue
        longitude, latitude = coordinates[0], coordinates[1]
        if area.contains(latitude, longitude):
            positions.append(feature)
    return positions


def build_ship_features(
    positions: list[dict[str, Any]],
    register: VesselRegister,
    icebreakers: set[int],
    config: ShipFeedConfig,
    texts: Texts,
) -> list[dict[str, Any]]:
    features = []
    for position in positions:
        props = position["properties"]
        mmsi = int(props["mmsi"])
        meta = register.get(mmsi) or {}
        category = ship_type(meta.get("shipType"))
        is_icebreaker = mmsi in icebreakers

        # Icebreakers are always shown, whatever the filters.
        if not is_icebreaker:
            if not config.include_moored and is_moored(props.get("navStat")):
                continue
            if config.ship_types is not None and category not in config.ship_types:
                continue

        kind = "icebreaker" if is_icebreaker else category
        longitude, latitude = position["geometry"]["coordinates"][:2]
        knots = speed_knots(props)
        features.append(
            point_feature(
                f"ship:{mmsi}",
                latitude,
                longitude,
                {
                    "name": str(meta.get("name") or "").strip() or f"MMSI {mmsi}",
                    "kind": f"ship.{kind}",
                    "updated": iso_from_epoch_ms(props.get("timestampExternal")),
                    "heading": ship_heading(props),
                    "stationary": is_stationary(props),
                    "speed_kmh": round(knots * KNOTS_TO_KMH, 1) if knots is not None else None,
                    "details": ship_details(props, meta, kind, texts),
                    "footer": ship_identifiers(mmsi, meta),
                },
            )
        )
    return features


def ship_details(props: Mapping[str, Any], meta: Mapping[str, Any], kind: str, texts: Texts) -> list[dict]:
    rows = [row(texts("type"), texts(f"ship_{kind}"))]

    nav_stat = props.get("navStat")
    if isinstance(nav_stat, int):
        rows.append(row(texts("status"), texts(navigation_status_key(nav_stat))))

    if destination := str(meta.get("destination") or "").strip():
        rows.append(row(texts("destination"), destination))

    draught = meta.get("draught")  # tenths of a metre
    if isinstance(draught, (int, float)) and 0 < draught < AIS_DRAUGHT_NOT_AVAILABLE:
        rows.append(row(texts("draught"), round(draught / 10, 1), "m"))

    # Reference points are distances from the AIS antenna to the bow, stern, port and starboard.
    length = (meta.get("referencePointA") or 0) + (meta.get("referencePointB") or 0)
    beam = (meta.get("referencePointC") or 0) + (meta.get("referencePointD") or 0)
    if length > 0 and beam > 0:
        rows.append(row(texts("size"), f"{length} × {beam}", "m"))

    return rows


def ship_identifiers(mmsi: int, meta: Mapping[str, Any]) -> str:
    identifiers = [f"MMSI {mmsi}"]
    if meta.get("imo"):
        identifiers.append(f"IMO {meta['imo']}")
    if call_sign := str(meta.get("callSign") or "").strip():
        identifiers.append(call_sign)
    return " · ".join(identifiers)
