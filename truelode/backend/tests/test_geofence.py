"""Geofence corridor checks."""
from app.services import geofence

CORRIDOR = [[-20.08, 31.80], [-18.90, 31.05], [-17.88, 30.70]]


def test_point_on_route_is_inside_buffer():
    off, dist = geofence.is_off_route(CORRIDOR, -18.90, 31.05, buffer_m=2000)
    assert off is False
    assert dist < 100


def test_point_far_off_route_flagged():
    # Well east of the corridor.
    off, dist = geofence.is_off_route(CORRIDOR, -18.90, 32.50, buffer_m=2000)
    assert off is True
    assert dist > 2000


def test_near_known_site():
    sites = [(-20.08, 31.80)]
    assert geofence.near_known_site(sites, -20.081, 31.801, radius_m=800) is True
    assert geofence.near_known_site(sites, -19.00, 31.00, radius_m=800) is False
