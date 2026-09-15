"""The area a feed covers, and geometry helpers. Coordinates are WGS84 decimal degrees.

GeoJSON positions are [longitude, latitude]; everything else here is latitude first.
Distances use a flat projection around the area, which is accurate to well under
a percent over the distances a feed covers.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

# Mean Earth radius (IUGG).
EARTH_RADIUS_KM = 6371.0088
KM_PER_DEGREE_LATITUDE = math.pi * EARTH_RADIUS_KM / 180

# 5 decimals is about 1 m: enough for a map, and it stops GPS noise from changing the state.
COORDINATE_DECIMALS = 5

# The longitudes and latitudes Digitraffic's bounding box parameters accept: (west, south, east, north).
BBOX_LIMITS = (19.0, 59.0, 32.0, 72.0)

type Position = Sequence[float]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


class LocalProjection:
    """Kilometres east and north of an origin."""

    def __init__(self, latitude: float, longitude: float) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._km_per_degree_longitude = KM_PER_DEGREE_LATITUDE * math.cos(math.radians(latitude))

    def project(self, position: Position) -> tuple[float, float]:
        """A GeoJSON position ([longitude, latitude]) as (east, north) kilometres."""
        return (
            (float(position[0]) - self._longitude) * self._km_per_degree_longitude,
            (float(position[1]) - self._latitude) * KM_PER_DEGREE_LATITUDE,
        )


def segment_distance(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> float:
    """Distance from a point to a line segment, in the units of the coordinates."""
    (px, py), (ax, ay), (bx, by) = point, start, end
    dx, dy = bx - ax, by - ay
    length_squared = dx * dx + dy * dy
    t = 0.0 if length_squared == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_squared))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_in_ring(point: tuple[float, float], ring: Sequence[tuple[float, float]]) -> bool:
    """Ray casting: whether a point is inside a closed ring."""
    x, y = point
    inside = False
    for (ax, ay), (bx, by) in pairwise(ring):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return inside


@dataclass(frozen=True)
class Area:
    """A circle around a point."""

    latitude: float
    longitude: float
    radius_km: float

    @classmethod
    def from_selector(cls, value: Mapping[str, Any]) -> Area:
        """From a location selector value: latitude, longitude and radius in metres."""
        return cls(float(value["latitude"]), float(value["longitude"]), float(value["radius"]) / 1000)

    def contains(self, latitude: Any, longitude: Any) -> bool:
        try:
            lat, lon = float(latitude), float(longitude)
        except (TypeError, ValueError):
            return False
        if not (math.isfinite(lat) and math.isfinite(lon)):
            return False
        return haversine_km(self.latitude, self.longitude, lat, lon) <= self.radius_km

    def as_attribute(self) -> dict[str, Any]:
        """The `area` attribute of the Map Feed format (latitude first)."""
        return {
            "center": [round(self.latitude, 5), round(self.longitude, 5)],
            "radius_km": round(self.radius_km, 3),
        }

    def bbox(self) -> tuple[float, float, float, float]:
        """(west, south, east, north) around the circle, within what Digitraffic accepts."""
        d_lat = self.radius_km / KM_PER_DEGREE_LATITUDE
        d_lon = self.radius_km / (KM_PER_DEGREE_LATITUDE * max(math.cos(math.radians(self.latitude)), 0.01))
        west, south, east, north = BBOX_LIMITS
        return (
            round(max(west, self.longitude - d_lon), 4),
            round(max(south, self.latitude - d_lat), 4),
            round(min(east, self.longitude + d_lon), 4),
            round(min(north, self.latitude + d_lat), 4),
        )

    def touches(self, geometry: Mapping[str, Any] | None) -> bool:
        """Whether a GeoJSON geometry is at least partly inside the circle."""
        if not isinstance(geometry, Mapping):
            return False
        projection = LocalProjection(self.latitude, self.longitude)
        coordinates = geometry.get("coordinates")
        try:
            match geometry.get("type"):
                case "Point":
                    return self._near(projection, [coordinates])
                case "LineString":
                    return self._near(projection, coordinates)
                case "MultiLineString":
                    return any(self._near(projection, path) for path in coordinates)
                case "Polygon":
                    return self._touches_polygon(projection, coordinates)
                case "MultiPolygon":
                    return any(self._touches_polygon(projection, polygon) for polygon in coordinates)
        except (TypeError, ValueError, IndexError):
            return False
        return False

    def _near(self, projection: LocalProjection, path: Sequence[Position]) -> bool:
        points = [projection.project(position) for position in path]
        if len(points) == 1:
            return math.hypot(*points[0]) <= self.radius_km
        return any(segment_distance((0.0, 0.0), start, end) <= self.radius_km for start, end in pairwise(points))

    def _touches_polygon(self, projection: LocalProjection, rings: Sequence[Sequence[Position]]) -> bool:
        if any(self._near(projection, ring) for ring in rings):
            return True
        # The whole circle can lie inside a large polygon, such as a municipality.
        return bool(rings) and point_in_ring((0.0, 0.0), [projection.project(position) for position in rings[0]])


def round_position(position: Position) -> list[float]:
    """[longitude, latitude] rounded, without an altitude."""
    return [round(float(position[0]), COORDINATE_DECIMALS), round(float(position[1]), COORDINATE_DECIMALS)]


def simplify_path(path: Sequence[Position], tolerance_km: float) -> list[list[float]]:
    """Douglas–Peucker: leaves out points closer than the tolerance to the simplified line.

    Road geometries from Digitraffic can have thousands of points; a map needs a
    few dozen. The result is rounded and has no repeated points.
    """
    if len(path) > 2:
        projection = LocalProjection(float(path[0][1]), float(path[0][0]))
        points = [projection.project(position) for position in path]
        keep = [False] * len(path)
        keep[0] = keep[-1] = True
        stack = [(0, len(path) - 1)]
        while stack:
            start, end = stack.pop()
            farthest, distance = -1, tolerance_km
            for index in range(start + 1, end):
                offset = segment_distance(points[index], points[start], points[end])
                if offset > distance:
                    farthest, distance = index, offset
            if farthest >= 0:
                keep[farthest] = True
                stack.extend(((start, farthest), (farthest, end)))
        path = [position for position, kept in zip(path, keep, strict=True) if kept]

    result: list[list[float]] = []
    for position in path:
        rounded = round_position(position)
        if not result or rounded != result[-1]:
            result.append(rounded)
    return result


def simplify_geometry(geometry: Mapping[str, Any] | None, tolerance_km: float) -> dict[str, Any] | None:
    """A simplified, rounded copy of a GeoJSON geometry; None when nothing drawable is left."""
    if not isinstance(geometry, Mapping):
        return None
    coordinates = geometry.get("coordinates")
    try:
        match geometry.get("type"):
            case "Point":
                return {"type": "Point", "coordinates": round_position(coordinates)}
            case "LineString":
                return line_geometry([simplify_path(coordinates, tolerance_km)])
            case "MultiLineString":
                return line_geometry([simplify_path(path, tolerance_km) for path in coordinates])
            case "Polygon":
                return polygon_geometry([simplify_rings(coordinates, tolerance_km)])
            case "MultiPolygon":
                return polygon_geometry([simplify_rings(polygon, tolerance_km) for polygon in coordinates])
    except (TypeError, ValueError, IndexError):
        return None
    return None


def simplify_rings(rings: Sequence[Sequence[Position]], tolerance_km: float) -> list[list[list[float]]]:
    simplified = [simplify_path(ring, tolerance_km) for ring in rings]
    # A ring needs at least three corners and the closing point.
    return [ring for ring in simplified if len(ring) >= 4]


def line_geometry(paths: Sequence[list[list[float]]]) -> dict[str, Any] | None:
    """A LineString for one path, a MultiLineString for several; None when no path has two points."""
    valid = [path for path in paths if len(path) >= 2]
    if not valid:
        return None
    if len(valid) == 1:
        return {"type": "LineString", "coordinates": valid[0]}
    return {"type": "MultiLineString", "coordinates": valid}


def polygon_geometry(polygons: Sequence[list[list[list[float]]]]) -> dict[str, Any] | None:
    valid = [rings for rings in polygons if rings]
    if not valid:
        return None
    if len(valid) == 1:
        return {"type": "Polygon", "coordinates": valid[0]}
    return {"type": "MultiPolygon", "coordinates": valid}


def representative_position(geometry: Mapping[str, Any] | None) -> tuple[float, float] | None:
    """Where to put a marker for a geometry, as (latitude, longitude).

    The point itself, the middle of the longest line, or the average corner of a
    polygon's outer ring.
    """
    if not isinstance(geometry, Mapping):
        return None
    coordinates = geometry.get("coordinates")
    try:
        match geometry.get("type"):
            case "Point":
                return float(coordinates[1]), float(coordinates[0])
            case "LineString":
                return _middle_of([coordinates])
            case "MultiLineString":
                return _middle_of(coordinates)
            case "Polygon":
                return _ring_centre(coordinates[0])
            case "MultiPolygon":
                return _ring_centre(max((polygon[0] for polygon in coordinates), key=len))
    except (TypeError, ValueError, IndexError):
        return None
    return None


def _middle_of(paths: Sequence[Sequence[Position]]) -> tuple[float, float] | None:
    paths = [path for path in paths if path]
    if not paths:
        return None
    longest = max(paths, key=_path_length_km)
    lengths = [0.0]
    for start, end in pairwise(longest):
        lengths.append(lengths[-1] + haversine_km(float(start[1]), float(start[0]), float(end[1]), float(end[0])))
    half = lengths[-1] / 2
    index = next(index for index, length in enumerate(lengths) if length >= half)
    return float(longest[index][1]), float(longest[index][0])


def _path_length_km(path: Sequence[Position]) -> float:
    return sum(
        haversine_km(float(start[1]), float(start[0]), float(end[1]), float(end[0])) for start, end in pairwise(path)
    )


def _ring_centre(ring: Sequence[Position]) -> tuple[float, float] | None:
    corners = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    if not corners:
        return None
    return (
        sum(float(position[1]) for position in corners) / len(corners),
        sum(float(position[0]) for position in corners) / len(corners),
    )
