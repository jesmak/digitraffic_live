"""Traffic messages: road works, traffic announcements, weight restrictions and exempted transports.

Data: https://tie.digitraffic.fi/swagger/ (traffic-message v2). The messages
are published in Finnish only; labels, restriction types and work types are
written in the integration's language.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from .api import TRAFFIC_MESSAGE_PATHS, DigitrafficClient
from .const import CONF_AREA, CONF_MESSAGE_TYPES, CONF_UPCOMING_DAYS, DEFAULT_UPCOMING_DAYS
from .feed import format_time, number_text, point_feature, row, shape_feature, time_range, utc_iso
from .geo import Area, representative_position, simplify_geometry
from .texts import Texts

# Message type setting values, in display order.
MESSAGE_TYPES = tuple(TRAFFIC_MESSAGE_PATHS)

# Feed kinds by the API's situation type. Accident reports are traffic announcements with their own kind.
SITUATION_KINDS = {
    "road work": "road.roadwork",
    "traffic announcement": "road.announcement",
    "weight restriction": "road.weight_restriction",
    "exempted transport": "road.exempted_transport",
}

# Road geometries come with a point every few metres; 20 m is invisible on a map and cuts most of them.
SIMPLIFY_TOLERANCE_KM = 0.02

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


@dataclass(frozen=True)
class TrafficMessageFeedConfig:
    area: Area
    message_types: tuple[str, ...]
    # Road works starting within this many days are included; 0 = only those in force now.
    upcoming_days: int

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> TrafficMessageFeedConfig:
        """From config subentry data. No message types chosen means all of them."""
        chosen = set(data.get(CONF_MESSAGE_TYPES) or ())
        return cls(
            area=Area.from_selector(data[CONF_AREA]),
            message_types=tuple(kind for kind in MESSAGE_TYPES if kind in chosen) or MESSAGE_TYPES,
            upcoming_days=int(data.get(CONF_UPCOMING_DAYS, DEFAULT_UPCOMING_DAYS)),
        )


async def fetch_traffic_messages(
    client: DigitrafficClient, config: TrafficMessageFeedConfig, now: datetime
) -> list[dict[str, Any]]:
    """Messages of the chosen types that touch the area."""
    until = utc_iso(now + timedelta(days=config.upcoming_days))
    bbox = config.area.bbox()
    responses = await asyncio.gather(
        *(client.traffic_messages(message_type, bbox, until) for message_type in config.message_types)
    )
    return [
        feature
        for response in responses
        for feature in (response or {}).get("features") or []
        if config.area.touches(feature.get("geometry"))
    ]


def build_traffic_message_features(
    situations: Sequence[Mapping[str, Any]], texts: Texts, now: datetime
) -> list[dict[str, Any]]:
    """A warning sign for each message, and the stretch of road or area it covers."""
    features: list[dict[str, Any]] = []
    for situation in situations:
        props = situation.get("properties") or {}
        situation_id = props.get("situationId")
        announcement = pick_announcement(props.get("announcements"), texts.language)
        position = representative_position(situation.get("geometry"))
        if not situation_id or announcement is None or position is None:
            continue

        kind = situation_kind(props)
        point_id = f"traffic_message:{situation_id}"
        latitude, longitude = position
        features.append(
            point_feature(
                point_id,
                latitude,
                longitude,
                {
                    "name": message_title(announcement),
                    "kind": kind,
                    "updated": props.get("versionTime") or props.get("releaseTime"),
                    "subtitle": first_line((announcement.get("location") or {}).get("description")),
                    "details": message_details(announcement, texts, now),
                    "notices": [comment] if (comment := str(announcement.get("comment") or "").strip()) else None,
                    "footer": announcement.get("sender"),
                },
            )
        )

        geometry = simplify_geometry(situation.get("geometry"), SIMPLIFY_TOLERANCE_KM)
        if geometry is not None and geometry["type"] != "Point":
            features.append(shape_feature(f"{point_id}/area", geometry, {"kind": kind, "point": point_id}))
    return features


# ---------------- interpreting messages ----------------


def situation_kind(props: Mapping[str, Any]) -> str:
    if props.get("trafficAnnouncementType") == "accident report":
        return "road.accident"
    return SITUATION_KINDS.get(str(props.get("situationType")), "road.announcement")


def pick_announcement(announcements: Any, language: str) -> Mapping[str, Any] | None:
    """The announcement in the chosen language if there is one, otherwise the first."""
    if not isinstance(announcements, list) or not announcements:
        return None
    return next((item for item in announcements if item.get("language") == language), announcements[0])


def message_title(announcement: Mapping[str, Any]) -> str:
    """ "Tie 26, Hamina, Luumäki. Tietyö. " → "Tie 26, Hamina, Luumäki. Tietyö" """
    return str(announcement.get("title") or "").strip().rstrip(".").strip()


def first_line(text: Any) -> str:
    return str(text or "").strip().split("\n", 1)[0].strip()


def message_details(announcement: Mapping[str, Any], texts: Texts, now: datetime) -> list[dict[str, Any]]:
    rows = []
    phases = [phase for phase in announcement.get("roadWorkPhases") or [] if isinstance(phase, Mapping)]
    phase = current_phase(phases, now)
    timing = (phase or announcement).get("timeAndDuration") or {}

    if status := message_status(timing.get("startTime"), texts, now):
        rows.append(row(texts("status"), status))
    if period := time_range(timing.get("startTime"), timing.get("endTime"), texts):
        rows.append(row(texts("time"), period))
    if phase is not None:
        if hours := working_hours(phase.get("workingHours"), texts):
            rows.append(row(texts("working_hours"), hours))
        if work := work_type_texts(phase.get("workTypes"), texts):
            rows.append(row(texts("work"), work))
        if restrictions := restriction_texts(phase.get("restrictions"), texts):
            rows.append(row(texts("restrictions"), restrictions))
        if len(phases) > 1:
            rows.append(row(texts("phases"), len(phases)))
    if effects := feature_texts(announcement.get("features")):
        rows.append(row(texts("effects"), effects))
    if route := itinerary_text(announcement.get("lastActiveItinerarySegment"), texts):
        rows.append(row(texts("route"), route))
    return rows


def current_phase(phases: Sequence[Mapping[str, Any]], now: datetime) -> Mapping[str, Any] | None:
    """The road work phase in force now, otherwise the next one to start, otherwise the last one."""
    if not phases:
        return None
    upcoming = []
    for phase in phases:
        timing = phase.get("timeAndDuration") or {}
        start = dt_util.parse_datetime(timing.get("startTime") or "")
        end = dt_util.parse_datetime(timing.get("endTime") or "")
        if start is not None and start > now:
            upcoming.append((start, phase))
        elif end is None or end > now:
            return phase
    if upcoming:
        return min(upcoming, key=lambda item: item[0])[1]
    return phases[-1]


def message_status(start: str | None, texts: Texts, now: datetime) -> str:
    begins = dt_util.parse_datetime(start or "")
    if begins is not None and begins > now:
        return texts("starts", time=format_time(start, texts.language))
    return texts("active")


def working_hours(hours: Any, texts: Texts) -> str:
    """ "Mon–Fri 18.00–06.00; Sat 08.00–16.00", days with the same hours together."""
    if not isinstance(hours, list):
        return ""
    by_time: dict[tuple[str, str], list[int]] = {}
    for item in hours:
        if not isinstance(item, Mapping) or item.get("weekday") not in WEEKDAYS:
            continue
        span = (str(item.get("startTime") or ""), str(item.get("endTime") or ""))
        by_time.setdefault(span, []).append(WEEKDAYS.index(item["weekday"]))
    parts = []
    for (start, end), days in sorted(by_time.items(), key=lambda entry: min(entry[1])):
        names = day_names(days, texts)
        separator = ":" if texts.language == "en" else "."
        parts.append(f"{names} {start.replace(':', separator)}–{end.replace(':', separator)}")
    return "; ".join(parts)


def day_names(days: Sequence[int], texts: Texts) -> str:
    """ "Mon–Fri", "Mon, Wed", "Mon, Tue": three or more days in a row become a range."""
    ordered = sorted(set(days))
    runs: list[list[int]] = []
    for day in ordered:
        if runs and day == runs[-1][-1] + 1:
            runs[-1].append(day)
        else:
            runs.append([day])

    def name(day: int) -> str:
        return texts(f"weekday_{WEEKDAYS[day].lower()}")

    parts = []
    for run in runs:
        if len(run) >= 3:
            parts.append(f"{name(run[0])}–{name(run[-1])}")
        else:
            parts.extend(name(day) for day in run)
    return ", ".join(parts)


def work_type_texts(work_types: Any, texts: Texts) -> str:
    names = []
    for item in work_types if isinstance(work_types, list) else []:
        if not isinstance(item, Mapping):
            continue
        work_type = str(item.get("type") or "")
        description = str(item.get("description") or "").strip()
        key = f"work_{work_type.replace(' ', '_')}"
        if work_type == "other" and description:
            names.append(description)
        elif texts.has(key):
            names.append(texts(key))
        elif description:
            names.append(description)
    return ", ".join(dict.fromkeys(names))


def restriction_texts(restrictions: Any, texts: Texts) -> str:
    """ "One lane closed, speed limit 50 km/h" """
    names = []
    for item in restrictions if isinstance(restrictions, list) else []:
        if not isinstance(item, Mapping):
            continue
        detail = item.get("restriction") or {}
        key = f"restriction_{str(item.get('type') or '').replace(' ', '_')}"
        name = texts(key) if texts.has(key) else str(detail.get("name") or "").strip()
        if name:
            names.append(join_quantity(name, detail.get("quantity"), detail.get("unit")))
    return ", ".join(dict.fromkeys(names))


def feature_texts(features: Any) -> str:
    """The message's own descriptions of its effects, such as "Ajokaista suljettu liikenteeltä"."""
    names = []
    for item in features if isinstance(features, list) else []:
        if isinstance(item, Mapping) and (name := str(item.get("name") or "").strip()):
            names.append(join_quantity(name, item.get("quantity"), item.get("unit")))
    return ", ".join(dict.fromkeys(names))


def join_quantity(name: str, quantity: Any, unit: Any) -> str:
    if isinstance(quantity, (int, float)) and not isinstance(quantity, bool):
        return f"{name} {number_text(quantity)} {unit or ''}".strip()
    return name


def itinerary_text(segment: Any, texts: Texts) -> str:
    """An exempted transport's current legs: "Road 28: Kärsämäki – Mainua; Road 5: Mainua – Kajaani"."""
    if not isinstance(segment, Mapping):
        return ""
    legs = []
    for leg in segment.get("legs") or []:
        road = (leg or {}).get("roadLeg") or {}
        if road.get("roadNumber"):
            legs.append(
                texts(
                    "road_leg",
                    road=road["roadNumber"],
                    start=road.get("startArea") or "",
                    end=road.get("endArea") or "",
                )
            )
        elif street := (leg or {}).get("streetName"):
            legs.append(str(street))
    return "; ".join(legs)
