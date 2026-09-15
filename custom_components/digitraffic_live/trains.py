"""Trains: running trains from the railway GraphQL API as map feed features."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DEPARTURE_DATE,
    ATTR_TRAIN_NUMBER,
    CONF_AREA,
    CONF_CATEGORIES,
    CONF_MAX_AGE_MINUTES,
    CONF_ROUTE,
    DEFAULT_TRAIN_MAX_AGE_MINUTES,
    DOMAIN,
    SERVICE_GET_TRAIN_COMPOSITION,
)
from .feed import point_feature, row
from .geo import Area
from .texts import Texts

# Category setting values and the names the railway API uses for them.
TRAIN_CATEGORIES: dict[str, str] = {
    "long_distance": "Long-distance",
    "commuter": "Commuter",
    "cargo": "Cargo",
    "locomotive": "Locomotive",
    "test_drive": "Test drive",
    "on_track_machines": "On-track machines",
    "shunting": "Shunting",
}

# Feed kinds by API category name. Everything else is "train.other".
CATEGORY_KINDS: dict[str, str] = {
    "Long-distance": "train.long_distance",
    "Commuter": "train.commuter",
    "Cargo": "train.cargo",
}

# Services listed in the composition, in display order. Each is also a text key.
TRAIN_SERVICES = ("catering", "pet", "playground", "disabled", "luggage", "video")

# One request returns everything a feed needs: position, type, the last station
# passed (with delay), the next commercial stop (with estimate and track), and the
# first and last station for the route.
TRAIN_FIELDS = """
    trainNumber
    departureDate
    cancelled
    trainType { name trainCategory { name } }
    trainLocations(orderBy: {timestamp: DESCENDING}, take: 1) { speed timestamp location }
    last: timeTableRows(where: {actualTime: {unequals: null}}, orderBy: {scheduledTime: DESCENDING}, take: 1) {
      station { name shortCode } type differenceInMinutes actualTime
    }
    next: timeTableRows(where: {and: [{actualTime: {equals: null}}, {commercialStop: {equals: true}}]}, orderBy: {scheduledTime: ASCENDING}, take: 1) {
      station { name shortCode } type scheduledTime liveEstimateTime differenceInMinutes commercialTrack cancelled
    }
    first: timeTableRows(orderBy: {scheduledTime: ASCENDING}, take: 1) { station { name } }
    destination: timeTableRows(orderBy: {scheduledTime: DESCENDING}, take: 1) { station { name } }"""


@dataclass(frozen=True)
class TrainFeedConfig:
    route: tuple[str, ...]  # station short codes; empty = no route filter
    categories: tuple[str, ...]  # API category names; empty = all
    area: Area | None
    max_age_minutes: int

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> TrainFeedConfig:
        """From config subentry data."""
        return cls(
            route=tuple(data.get(CONF_ROUTE) or ()),
            categories=tuple(
                TRAIN_CATEGORIES[key] for key in data.get(CONF_CATEGORIES) or () if key in TRAIN_CATEGORIES
            ),
            area=Area.from_selector(data[CONF_AREA]) if data.get(CONF_AREA) else None,
            max_age_minutes=int(data.get(CONF_MAX_AGE_MINUTES, DEFAULT_TRAIN_MAX_AGE_MINUTES)),
        )


# ---------------- query ----------------


def graphql_string(value: str) -> str:
    """A GraphQL string literal. JSON string syntax is valid GraphQL."""
    return json.dumps(value, ensure_ascii=False)


def build_train_query(route: Sequence[str] = (), categories: Sequence[str] = ()) -> str:
    """Trains with a commercial stop at every route station, in any of the categories."""
    conditions = [
        "{timeTableRows: {contains: {and: ["
        f"{{station: {{shortCode: {{equals: {graphql_string(code)}}}}}}}, "
        "{commercialStop: {equals: true}}]}}}"
        for code in route
    ]
    if categories:
        options = [
            f"{{trainType: {{trainCategory: {{name: {{equals: {graphql_string(name)}}}}}}}}}" for name in categories
        ]
        conditions.append(options[0] if len(options) == 1 else f"{{or: [{', '.join(options)}]}}")

    arguments = ""
    if len(conditions) == 1:
        arguments = f"(where: {conditions[0]})"
    elif conditions:
        arguments = f"(where: {{and: [{', '.join(conditions)}]}})"
    return f"{{ currentlyRunningTrains{arguments} {{{TRAIN_FIELDS}\n  }} }}"


# ---------------- interpreting train data ----------------


def first_row(train: Mapping[str, Any], alias: str) -> Mapping[str, Any]:
    rows = train.get(alias) or []
    return rows[0] if rows else {}


def delay_minutes(train: Mapping[str, Any]) -> int | None:
    """Minutes late at the last station passed, or at the next stop if none has been passed yet."""
    for alias in ("last", "next"):
        difference = first_row(train, alias).get("differenceInMinutes")
        if isinstance(difference, (int, float)):
            return int(difference)
    return None


def station_name(name: Any) -> str:
    """ "Helsinki asema" → "Helsinki"."""
    return re.sub(r" asema$", "", str(name or ""), flags=re.IGNORECASE)


def train_label(train: Mapping[str, Any]) -> str:
    """ "IC 8" """
    return f"{(train.get('trainType') or {}).get('name') or ''} {train.get('trainNumber') or ''}".strip()


def format_clock(value: str | None, language: str) -> str:
    """ "21.04" in Finnish and Swedish, "21:04" in English; "" when missing."""
    parsed = dt_util.parse_datetime(value) if value else None
    if parsed is None:
        return ""
    return dt_util.as_local(parsed).strftime("%H:%M" if language == "en" else "%H.%M")


def notice_key(train_number: Any, departure_date: Any) -> str:
    return f"{train_number}|{departure_date}"


def passenger_notice_index(messages: Any, language: str) -> dict[str, list[str]]:
    """Train-specific passenger notices by notice_key().

    Station-wide notices (without a train number) are left out. Texts are in the
    chosen language when available, otherwise Finnish, English or Swedish.
    """
    index: dict[str, list[str]] = {}
    for message in messages if isinstance(messages, list) else []:
        if not message.get("trainNumber") or not message.get("trainDepartureDate"):
            continue
        texts = (message.get("video") or {}).get("text") or (message.get("audio") or {}).get("text") or {}
        text = texts.get(language) or texts.get("fi") or texts.get("en") or texts.get("sv")
        if not text:
            continue
        notices = index.setdefault(notice_key(message["trainNumber"], message["trainDepartureDate"]), [])
        if text not in notices:
            notices.append(text)
    return index


def composition_details(data: Mapping[str, Any] | None, texts: Texts) -> list[dict[str, Any]]:
    """Popup rows for a composition: cars, top speed and services.

    A train can change composition on the way; the journey section with the
    most cars is used.
    """
    sections = (data or {}).get("journeySections") or []
    if not sections:
        return []
    largest = max(sections, key=lambda section: len(section.get("wagons") or []))
    wagons = largest.get("wagons") or []

    parts = [texts("cars", n=len(wagons))]
    if largest.get("maximumSpeed"):
        parts.append(texts("max_speed", n=largest["maximumSpeed"]))
    services = [texts(service) for service in TRAIN_SERVICES if any(wagon.get(service) for wagon in wagons)]
    if services:
        parts.append(", ".join(services))
    return [row(texts("composition"), " · ".join(parts))]


# ---------------- building the feed ----------------


def build_train_features(
    trains: list[dict[str, Any]],
    notices: Mapping[str, list[str]],
    config: TrainFeedConfig,
    texts: Texts,
    now: datetime,
) -> list[dict[str, Any]]:
    cutoff = now - timedelta(minutes=config.max_age_minutes)
    features = []
    for train in trains:
        location = first_row(train, "trainLocations")
        coordinates = location.get("location") or []
        measured = dt_util.parse_datetime(location.get("timestamp") or "")
        if len(coordinates) < 2 or measured is None or measured < cutoff:
            continue
        longitude, latitude = coordinates[0], coordinates[1]
        if config.area is not None and not config.area.contains(latitude, longitude):
            continue

        label = train_label(train)
        origin = station_name(first_row(train, "first").get("station", {}).get("name"))
        destination = station_name(first_row(train, "destination").get("station", {}).get("name"))
        category = ((train.get("trainType") or {}).get("trainCategory") or {}).get("name")

        features.append(
            point_feature(
                f"train:{train['departureDate']}/{train['trainNumber']}",
                latitude,
                longitude,
                {
                    "name": label,
                    "kind": CATEGORY_KINDS.get(category, "train.other"),
                    "updated": location.get("timestamp"),
                    "speed_kmh": location.get("speed"),
                    "delay_minutes": delay_minutes(train),
                    "cancelled": True if train.get("cancelled") else None,
                    "badge": label,
                    "label": f"→ {destination}" if destination else None,
                    "subtitle": f"{origin} → {destination}" if origin and destination else None,
                    "details": train_details(train, texts),
                    "notices": notices.get(notice_key(train["trainNumber"], train["departureDate"])),
                    "detail_action": {
                        "action": f"{DOMAIN}.{SERVICE_GET_TRAIN_COMPOSITION}",
                        "data": {
                            ATTR_DEPARTURE_DATE: train["departureDate"],
                            ATTR_TRAIN_NUMBER: train["trainNumber"],
                        },
                    },
                },
            )
        )
    return features


def train_details(train: Mapping[str, Any], texts: Texts) -> list[dict[str, Any]]:
    rows = []

    if last := first_row(train, "last"):
        clock = format_clock(last.get("actualTime"), texts.language)
        rows.append(row(texts("passed"), join_words(station_name(last.get("station", {}).get("name")), clock)))

    if upcoming := first_row(train, "next"):
        clock = format_clock(upcoming.get("liveEstimateTime") or upcoming.get("scheduledTime"), texts.language)
        value = join_words(station_name(upcoming.get("station", {}).get("name")), clock)
        if track := upcoming.get("commercialTrack"):
            value += f", {texts('track')} {track}"
        if upcoming.get("cancelled"):
            value += f" ({texts('cancelled')})"
        rows.append(row(texts("next_stop"), value))

    return rows


def join_words(*words: str) -> str:
    return " ".join(word for word in words if word)
