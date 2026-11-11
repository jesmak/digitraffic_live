"""Nautical warnings: lights out of order, dredging, firing exercises and other hazards to boats and ships.

Data: Traficom's open WFS, the layers navigational_warnings_a (areas), _l (lines) and _p (points). They hold the
warnings in force for the whole country, the inland waters included, with their texts in Finnish, Swedish and
English. A warning has no end time: it ends by leaving the layers.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .api import NAUTICAL_WARNING_LAYERS, DigitrafficClient
from .const import CONF_AREA
from .feed import point_feature, row, shape_feature
from .geo import Area, representative_position, simplify_geometry
from .texts import Texts

KIND = "sea.warning"

# Drops only points that add nothing to a shape.
SIMPLIFY_TOLERANCE_KM = 0.005


@dataclass(frozen=True)
class NauticalWarningFeedConfig:
    area: Area

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> NauticalWarningFeedConfig:
        return cls(area=Area.from_selector(data[CONF_AREA]))


async def fetch_nautical_warnings(client: DigitrafficClient, config: NauticalWarningFeedConfig) -> list[dict[str, Any]]:
    """The warnings in force that touch the area."""
    responses = await asyncio.gather(*(client.nautical_warnings(layer) for layer in NAUTICAL_WARNING_LAYERS))
    return [
        feature
        for response in responses
        for feature in (response or {}).get("features") or []
        if config.area.touches(drawable_geometry(feature.get("geometry")))
    ]


def build_nautical_warning_features(warnings: Sequence[Mapping[str, Any]], texts: Texts) -> list[dict[str, Any]]:
    """A warning sign for each warning, and the area or line it covers."""
    features: list[dict[str, Any]] = []
    for warning in warnings:
        props = warning.get("properties") or {}
        warning_id = props.get("MESSAGESERIESIDENTIFIERINTEROPERABILITYIDENTIFIER")
        geometry = drawable_geometry(warning.get("geometry"))
        position = representative_position(geometry)
        if not warning_id or position is None:
            continue

        general_type = localized(props, "NAVWARNTYPEGENERAL", texts.language)
        detailed_type = localized(props, "WARNINGINFORMATIONNAVWARNTYPEDETAILS", texts.language)
        sea_area = localized(props, "GENERALAREALOCATIONNAME", texts.language)
        point_id = f"nautical_warning:{warning_id}"
        latitude, longitude = position
        features.append(
            point_feature(
                point_id,
                latitude,
                longitude,
                {
                    "name": detailed_type or general_type or texts("nautical_warning"),
                    "kind": KIND,
                    "updated": props.get("PUBLICATIONTIME"),
                    "subtitle": localized(props, "LOCALITYLOCATIONNAME", texts.language),
                    "details": [
                        *([row(texts("type"), general_type)] if detailed_type and general_type else []),
                        *([row(texts("warning_area"), sea_area)] if sea_area else []),
                    ],
                    "notices": [text] if (text := warning_text(props, texts.language)) else None,
                    "footer": series_and_number(props, texts.language),
                },
            )
        )

        shape = simplify_geometry(geometry, SIMPLIFY_TOLERANCE_KM)
        if shape is not None and shape["type"] != "Point":
            features.append(shape_feature(f"{point_id}/area", shape, {"kind": KIND, "point": point_id}))
    return features


def drawable_geometry(geometry: Any) -> Any:
    """The points layer's geometries are MultiPoints of one point, which the feed draws as that point."""
    if isinstance(geometry, Mapping) and geometry.get("type") == "MultiPoint" and geometry.get("coordinates"):
        return {"type": "Point", "coordinates": geometry["coordinates"][0]}
    return geometry


def localized(props: Mapping[str, Any], field: str, language: str) -> str:
    """A field's text in the feed's language, in Finnish when it has none."""
    return str(props.get(f"{field}_{language.upper()}") or props.get(f"{field}_FI") or "").strip()


def warning_text(props: Mapping[str, Any], language: str) -> str:
    """The warning as one paragraph. Some are written on several lines, with empty ones between."""
    return " ".join(localized(props, "WARNINGINFORMATION", language).split())


def series_and_number(props: Mapping[str, Any], language: str) -> str:
    """ "Warnings for Yachtmen 139/2026" """
    series = localized(props, "MESSAGESERIESIDENTIFIERNAMEOFSERIES", language)
    number = props.get("MESSAGESERIESIDENTIFIERWARNINGNUMBER")
    year = props.get("MESSAGESERIESIDENTIFIERYEAR")
    if number is None or year is None:
        return series
    return f"{series} {number}/{year}".strip()
