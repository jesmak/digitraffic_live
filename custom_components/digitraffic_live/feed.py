"""Building blocks of the Map Feed format.

The format is documented in docs/map-feed-format.md of ha-map-card-plugin-map-feed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .geo import COORDINATE_DECIMALS
from .texts import Texts


def point_feature(feature_id: str, latitude: float, longitude: float, properties: dict[str, Any]) -> dict[str, Any]:
    """A GeoJSON Point feature. Properties without a value are left out, as the format asks."""
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "Point",
            # GeoJSON order: longitude first.
            "coordinates": [
                round(float(longitude), COORDINATE_DECIMALS),
                round(float(latitude), COORDINATE_DECIMALS),
            ],
        },
        "properties": {key: value for key, value in properties.items() if value not in (None, "", [])},
    }


def shape_feature(feature_id: str, geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    """A LineString, MultiLineString, Polygon or MultiPolygon feature. The geometry must already be rounded."""
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": geometry,
        "properties": {key: value for key, value in properties.items() if value not in (None, "", [])},
    }


def feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def row(label: str, value: str | float, unit: str | None = None) -> dict[str, Any]:
    """One popup row."""
    result: dict[str, Any] = {"label": label, "value": value}
    if unit:
        result["unit"] = unit
    return result


def iso_from_epoch_ms(value: Any) -> str | None:
    """Milliseconds since the epoch as an ISO 8601 UTC time, or None when not a number."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return dt_util.utc_from_timestamp(value / 1000).isoformat(timespec="seconds")


def format_time(value: str | None, language: str, with_date: bool = True) -> str:
    """ "20.9. 21.04" in Finnish and Swedish, "20.9. 21:04" in English, in local time; "" when missing."""
    parsed = dt_util.parse_datetime(value) if value else None
    if parsed is None:
        return ""
    local = dt_util.as_local(parsed)
    clock = local.strftime("%H:%M" if language == "en" else "%H.%M")
    return f"{local.day}.{local.month}. {clock}" if with_date else clock


def time_range(start: str | None, end: str | None, texts: Texts) -> str:
    """ "20.9. 21.00 – 2.10. 23.59", "from 20.9. 21.00", "until 2.10. 23.59", or ""."""
    first = format_time(start, texts.language)
    last = format_time(end, texts.language)
    if first and last:
        return f"{first} – {last}"
    if first:
        return texts("from_time", time=first)
    if last:
        return texts("until_time", time=last)
    return ""


def utc_iso(moment: datetime) -> str:
    """A time as Digitraffic's query parameters expect it: 2026-09-15T12:00:00Z."""
    return moment.astimezone(dt_util.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def number_text(value: float, decimals: int = 1) -> str:
    """ "2.5", and "3" rather than "3.0"."""
    text = f"{value:.{decimals}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text
