"""Road maintenance: where snow ploughs, gritters and other maintenance vehicles are, and where they have worked.

Data: https://tie.digitraffic.fi/swagger/ (maintenance/v1/tracking). It covers
state roads, maintained under Fintraffic's contracts; most city streets are not included.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .api import DigitrafficClient
from .const import (
    CONF_AREA,
    CONF_MAX_AGE_MINUTES,
    CONF_ROUTE_HOURS,
    CONF_SHOW_ROUTES,
    CONF_TASKS,
    DEFAULT_MAINTENANCE_MAX_AGE_MINUTES,
    DEFAULT_ROUTE_HOURS,
)
from .feed import point_feature, row, shape_feature, time_range, utc_iso
from .geo import Area, haversine_km, line_geometry, simplify_path
from .texts import Texts

# Task ids of the maintenance tracking API. The task setting stores them in lower case, as Home Assistant
# requires for selector options.
MAINTENANCE_TASKS = (
    "BRUSHING",
    "BRUSH_CLEARING",
    "CLEANSING_OF_BRIDGES",
    "CLEANSING_OF_REST_AREAS",
    "CLEANSING_OF_TRAFFIC_SIGNS",
    "CLIENTS_QUALITY_CONTROL",
    "COMPACTION_BY_ROLLING",
    "CRACK_FILLING",
    "DITCHING",
    "DUST_BINDING_OF_GRAVEL_ROAD_SURFACE",
    "DUST_BINDING_OF_PAVED_ROAD_SURFACE",
    "ENSURING_TRAFFIC_IN_RASPUTITSA",
    "FILLING_OF_GRAVEL_ROAD_SHOULDERS",
    "FILLING_OF_ROAD_SHOULDERS",
    "GARBAGE_OLLECTION",
    "GROUP_REPLACEMENT_OF_LAMPS",
    "HEATING",
    "LEVELLING_GRAVEL_ROAD_SURFACE",
    "LEVELLING_OF_ROAD_SHOULDERS",
    "LEVELLING_OF_ROAD_SHOULDERS_UNDER_RAILING",
    "LEVELLING_OF_ROAD_SURFACE",
    "LINE_SANDING",
    "LOWERING_OF_SNOWBANKS",
    "MAINTENANCE_OF_GUIDE_SIGNS_AND_REFLECTOR_POSTS",
    "MECHANICAL_CUT",
    "MIXING_OR_STABILIZATION",
    "OTHER",
    "OTHER_OPERATIONS_OF_LIGHTING_CONTRACTS",
    "PATCHING",
    "PAVING",
    "PLOUGHING_AND_SLUSH_REMOVAL",
    "PLOUGHING_OF_SLUSH_DITCH",
    "PREVENTING_MELTING_WATER_PROBLEMS",
    "REMOVAL_OF_BULGE_ICE",
    "RENEWAL_OF_EDGE_COLUMNS",
    "RESHAPING_GRAVEL_ROAD_SURFACE",
    "ROAD_INSPECTIONS",
    "ROAD_MARKINGS",
    "ROAD_STATE_CHECKING",
    "SAFETY_EQUIPMENT",
    "SALTING",
    "SERVICE_ROUND",
    "SNOW_PLOUGHING_STICKS_AND_SNOW_FENCES",
    "SPOT_SANDING",
    "SPREADING_OF_CRUSH",
    "TRANSFER_OF_SNOW",
    "UNKNOWN",
)

# Digitraffic keeps routes for 24 hours.
MAX_ROUTE_HOURS = 24
# Consecutive route pieces further apart than this are drawn as separate lines.
ROUTE_GAP_KM = 0.5
SIMPLIFY_TOLERANCE_KM = 0.01


@dataclass(frozen=True)
class MaintenanceFeedConfig:
    area: Area
    tasks: tuple[str, ...]  # empty = all tasks
    max_age_minutes: int
    show_routes: bool
    route_hours: int

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> MaintenanceFeedConfig:
        chosen = {str(task).upper() for task in data.get(CONF_TASKS) or ()}
        return cls(
            area=Area.from_selector(data[CONF_AREA]),
            tasks=tuple(task for task in MAINTENANCE_TASKS if task in chosen),
            max_age_minutes=int(data.get(CONF_MAX_AGE_MINUTES, DEFAULT_MAINTENANCE_MAX_AGE_MINUTES)),
            show_routes=bool(data.get(CONF_SHOW_ROUTES, True)),
            route_hours=min(MAX_ROUTE_HOURS, max(1, int(data.get(CONF_ROUTE_HOURS, DEFAULT_ROUTE_HOURS)))),
        )


async def fetch_maintenance(
    client: DigitrafficClient, config: MaintenanceFeedConfig, now: datetime
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Latest vehicle positions, and routes if they are shown, inside the area."""
    bbox = config.area.bbox()
    requests = [client.maintenance_latest(bbox, utc_iso(now - timedelta(minutes=config.max_age_minutes)), config.tasks)]
    if config.show_routes:
        requests.append(
            client.maintenance_routes(bbox, utc_iso(now - timedelta(hours=config.route_hours)), config.tasks)
        )
    responses = await asyncio.gather(*requests)

    def inside(response: Any, geometry_types: set[str]) -> list[dict[str, Any]]:
        return [
            feature
            for feature in (response or {}).get("features") or []
            if (feature.get("geometry") or {}).get("type") in geometry_types
            and config.area.touches(feature.get("geometry"))
        ]

    vehicles = inside(responses[0], {"Point"})
    routes = inside(responses[1], {"LineString"}) if config.show_routes else []
    return vehicles, routes


def task_names(tasks: Any, language: str) -> dict[str, str]:
    """Task names in the chosen language, by task id."""
    names = {}
    for task in tasks if isinstance(tasks, list) else []:
        if isinstance(task, Mapping) and task.get("id"):
            names[task["id"]] = task.get(f"name{language.capitalize()}") or task.get("nameFi") or task["id"]
    return names


def task_list(tasks: Sequence[str], names: Mapping[str, str]) -> str:
    return ", ".join(names.get(task, task.replace("_", " ").capitalize()) for task in tasks)


def build_maintenance_features(
    vehicles: Sequence[Mapping[str, Any]],
    routes: Sequence[Mapping[str, Any]],
    names: Mapping[str, str],
    texts: Texts,
) -> list[dict[str, Any]]:
    features = []
    for vehicle in vehicles:
        props = vehicle.get("properties") or {}
        coordinates = (vehicle.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) < 2 or props.get("id") is None:
            continue
        tasks = list(props.get("tasks") or [])
        direction = props.get("direction")
        moving = isinstance(direction, (int, float)) and not isinstance(direction, bool)
        features.append(
            point_feature(
                f"maintenance:{props['id']}",
                coordinates[1],
                coordinates[0],
                {
                    "name": task_list(tasks, names) or texts("maintenance_vehicle"),
                    "kind": "road.maintenance",
                    "updated": props.get("time"),
                    "heading": direction if moving else None,
                    "stationary": not moving,
                    "details": [
                        row(texts("tasks"), task_list(tasks, names)) if tasks else None,
                        row(texts("source"), props["source"]) if props.get("source") else None,
                    ],
                },
            )
        )
        features[-1]["properties"]["details"] = [item for item in features[-1]["properties"]["details"] if item]

    for chain in merge_routes(routes):
        geometry = line_geometry([simplify_path(path, SIMPLIFY_TOLERANCE_KM) for path in chain.paths])
        if geometry is None:
            continue
        features.append(
            shape_feature(
                f"maintenance_route:{chain.first_id}",
                geometry,
                {
                    "name": task_list(chain.tasks, names),
                    "kind": "road.maintenance_track",
                    "updated": chain.end,
                    "details": [
                        row(texts("worked"), time_range(chain.start, chain.end, texts)),
                        row(texts("tasks"), task_list(chain.tasks, names)),
                    ],
                },
            )
        )
    return features


@dataclass
class RouteChain:
    """One vehicle's route pieces for the same tasks, joined."""

    first_id: Any
    tasks: tuple[str, ...]
    start: str | None
    end: str | None
    paths: list[list[Sequence[float]]] = field(default_factory=list)


def merge_routes(routes: Sequence[Mapping[str, Any]]) -> list[RouteChain]:
    """Joins route pieces into lines.

    Digitraffic sends a vehicle's route in pieces of a few minutes, each naming
    the piece before it. Pieces that follow each other with the same tasks
    become one line; a gap in the route starts a new part of the same line.
    """
    pieces = sorted(
        (piece for piece in routes if len((piece.get("geometry") or {}).get("coordinates") or []) >= 2),
        key=lambda piece: str((piece.get("properties") or {}).get("startTime") or ""),
    )
    chains: list[RouteChain] = []
    by_last_piece: dict[Any, RouteChain] = {}
    for piece in pieces:
        props = piece.get("properties") or {}
        coordinates = [position[:2] for position in piece["geometry"]["coordinates"]]
        tasks = tuple(props.get("tasks") or ())
        previous = props.get("previousId")
        chain = by_last_piece.pop(previous, None) if previous is not None else None

        if chain is not None and chain.tasks == tasks:
            last = chain.paths[-1][-1]
            first = coordinates[0]
            if haversine_km(last[1], last[0], first[1], first[0]) > ROUTE_GAP_KM:
                chain.paths.append(coordinates)
            else:
                chain.paths[-1].extend(coordinates[1:] if list(first) == list(last) else coordinates)
            chain.end = props.get("endTime") or chain.end
        else:
            chain = RouteChain(props.get("id"), tasks, props.get("startTime"), props.get("endTime"), [coordinates])
            chains.append(chain)
        by_last_piece[props.get("id")] = chain
    return chains
