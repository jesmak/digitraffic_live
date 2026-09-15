"""Road conditions: Fintraffic's road weather observation and forecast for sections of the main roads.

Data: https://tie.digitraffic.fi/swagger/ (weather/v1/forecast-sections-simple).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .const import CONF_AREA, CONF_FORECAST, CONF_ONLY_POOR
from .feed import format_time, number_text, row, shape_feature
from .geo import Area, simplify_geometry
from .texts import Texts

# Forecast setting values: the observation now, and forecasts 2 to 12 hours ahead.
FORECAST_TIMES = ("0h", "2h", "4h", "6h", "12h")

CONDITIONS = {
    "NORMAL_CONDITION": "normal",
    "POOR_CONDITION": "poor",
    "EXTREMELY_POOR_CONDITION": "extremely_poor",
}
POOR_CONDITIONS = frozenset({"poor", "extremely_poor"})

# Reasons for the condition, each with a text key prefix. Values are the API's enums in lower case.
CONDITION_REASONS = (
    ("roadCondition", "road_surface", "surface"),
    ("frictionCondition", "friction", "friction"),
    ("precipitationCondition", "precipitation", "precipitation"),
    ("visibilityCondition", "visibility", "visibility"),
    ("windCondition", "wind", "wind"),
)

SIMPLIFY_TOLERANCE_KM = 0.05


@dataclass(frozen=True)
class RoadConditionFeedConfig:
    area: Area
    forecast: str
    only_poor: bool

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> RoadConditionFeedConfig:
        forecast = data.get(CONF_FORECAST)
        return cls(
            area=Area.from_selector(data[CONF_AREA]),
            forecast=forecast if forecast in FORECAST_TIMES else FORECAST_TIMES[0],
            only_poor=bool(data.get(CONF_ONLY_POOR, False)),
        )


def section_index(data: Any) -> dict[str, Mapping[str, Any]]:
    """Road sections by id, from the forecast sections list."""
    return {
        str(feature["id"]): feature
        for feature in (data or {}).get("features") or []
        if isinstance(feature, Mapping) and feature.get("id") is not None
    }


def build_road_condition_features(
    forecasts: Any,
    sections: Mapping[str, Mapping[str, Any]],
    config: RoadConditionFeedConfig,
    texts: Texts,
) -> list[dict[str, Any]]:
    features = []
    for section in (forecasts or {}).get("forecastSections") or []:
        section_id = str(section.get("id"))
        meta = sections.get(section_id)
        if meta is None or not config.area.touches(meta.get("geometry")):
            continue
        forecast = pick_forecast(section.get("forecasts"), config.forecast)
        if forecast is None:
            continue
        condition = CONDITIONS.get(str(forecast.get("overallRoadCondition")), "unknown")
        if config.only_poor and condition not in POOR_CONDITIONS:
            continue
        geometry = simplify_geometry(meta.get("geometry"), SIMPLIFY_TOLERANCE_KM)
        if geometry is None:
            continue

        props = meta.get("properties") or {}
        features.append(
            shape_feature(
                f"road_section:{section_id}",
                geometry,
                {
                    "name": props.get("description") or section_id,
                    "kind": f"road.condition.{condition}",
                    "updated": forecast.get("dataUpdatedTime"),
                    "subtitle": forecast_subtitle(forecast, texts),
                    "details": condition_details(condition, forecast, texts),
                },
            )
        )
    return features


def pick_forecast(forecasts: Any, name: str) -> Mapping[str, Any] | None:
    items = [item for item in forecasts if isinstance(item, Mapping)] if isinstance(forecasts, list) else []
    return next((item for item in items if item.get("forecastName") == name), items[0] if items else None)


def forecast_subtitle(forecast: Mapping[str, Any], texts: Texts) -> str:
    clock = format_time(forecast.get("time"), texts.language)
    if forecast.get("type") == "OBSERVATION":
        return texts("observed_at", time=clock) if clock else ""
    return texts("forecast_for", time=clock) if clock else ""


def condition_details(condition: str, forecast: Mapping[str, Any], texts: Texts) -> list[dict[str, Any]]:
    rows = [row(texts("road_condition"), texts(f"condition_{condition}"))]
    reasons = forecast.get("forecastConditionReason") or {}
    for field, label, prefix in CONDITION_REASONS:
        value = str(reasons.get(field) or "").lower()
        key = f"{prefix}_{value}"
        if value and texts.has(key):
            rows.append(row(texts(label), texts(key)))
    for field, label, unit in (
        ("roadTemperature", "road_temperature", "°C"),
        ("temperature", "air_temperature", "°C"),
        ("windSpeed", "wind_speed", "m/s"),
    ):
        value = forecast.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            rows.append(row(texts(label), number_text(value), unit))
    return rows


def count_poor(features: Sequence[Mapping[str, Any]]) -> int:
    """Sections with poor or extremely poor conditions: the feed sensor's state."""
    return sum(
        1
        for feature in features
        if feature["properties"].get("kind") in {f"road.condition.{condition}" for condition in POOR_CONDITIONS}
    )
