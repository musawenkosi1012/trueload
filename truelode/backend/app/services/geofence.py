"""GeofenceService: corridor adherence + unknown-stop detection (shapely)."""
import math

from shapely.geometry import LineString, Point

# Rough metres-per-degree near Zimbabwe's latitude; good enough for corridor checks.
_M_PER_DEG = 111_320.0


def _to_xy(lat: float, lng: float) -> tuple[float, float]:
    """Project lat/lng to local metres (equirectangular, fine for short corridors)."""
    x = lng * _M_PER_DEG * math.cos(math.radians(lat))
    y = lat * _M_PER_DEG
    return x, y


def distance_to_corridor_m(path: list[list[float]], lat: float, lng: float) -> float:
    """Shortest distance (m) from a point to the route polyline."""
    if not path or len(path) < 2:
        return 0.0
    line = LineString([_to_xy(p[0], p[1]) for p in path])
    return line.distance(Point(_to_xy(lat, lng)))


def is_off_route(path: list[list[float]], lat: float, lng: float,
                 buffer_m: float) -> tuple[bool, float]:
    d = distance_to_corridor_m(path, lat, lng)
    return d > buffer_m, d


def near_known_site(sites: list[tuple[float, float]], lat: float, lng: float,
                    radius_m: float = 800) -> bool:
    p = Point(_to_xy(lat, lng))
    return any(p.distance(Point(_to_xy(s[0], s[1]))) <= radius_m for s in sites)


def route_length_km(path: list[list[float]]) -> float:
    if not path or len(path) < 2:
        return 0.0
    line = LineString([_to_xy(p[0], p[1]) for p in path])
    return round(line.length / 1000.0, 1)
