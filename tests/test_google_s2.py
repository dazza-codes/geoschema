from typing import Generator

import pytest
import s2sphere
import shapely.geometry

from geoschema.google_s2 import point_to_s2_cell_id
from geoschema.google_s2 import point_to_s2_cell_token
from geoschema.google_s2 import points_to_s2_cell_token
from geoschema.google_s2 import s2_cell_id
from geoschema.google_s2 import s2_cell_to_lon_lat
from geoschema.google_s2 import s2_cell_token
from geoschema.proj_utils import LonLat


@pytest.fixture
def lon() -> float:
    return -80.179_799_067_338_82


@pytest.fixture
def lat() -> float:
    return +25.848_312_731_071_363


@pytest.fixture
def lonlat(lon, lat) -> LonLat:
    return LonLat(longitude=lon, latitude=lat)


@pytest.fixture
def lonlat_cell() -> s2sphere.CellId:
    # this is the expected CellId for the above lon,lat
    return s2sphere.CellId(9861110578328252229)


@pytest.fixture
def lonlat_point(lonlat) -> shapely.geometry.Point:
    return lonlat.point


def test_lonlat_to_s2_cell(lon, lat, lonlat_cell):
    s2_cell_expected = lonlat_cell
    s2_cell_returned = s2_cell_id(lon, lat)
    assert s2_cell_returned == s2_cell_expected
    assert s2_cell_returned.level() == 30
    assert s2_cell_returned.is_leaf()
    assert s2_cell_returned.is_valid()


def test_s2_cell_to_lonlat(lon, lat, lonlat_cell):
    s2_cell_expected = lonlat_cell
    s2_latlon = s2_cell_to_lon_lat(s2_cell_expected)
    lonlat = LonLat(longitude=s2_latlon.lng, latitude=s2_latlon.lat)
    assert lonlat.lon == pytest.approx(lon, abs=1e-6)
    assert lonlat.lat == pytest.approx(lat, abs=1e-6)
    s2_point = s2_cell_to_lon_lat(s2_cell_expected)
    assert lonlat.lon == pytest.approx(s2_point.lng, abs=1e-6)
    assert lonlat.lat == pytest.approx(s2_point.lat, abs=1e-6)


S2_LEVELS_TO_TOKENS = [
    (-1, 30, "879fe6242e7b2d95"),
    (31, 30, "879fe6242e7b2d95"),
    (28, 28, "879fe6242e7b2d9"),
    (24, 24, "879fe6242e7b3"),
    (18, 18, "879fe6242f"),
    (17, 17, "879fe6242c"),
    (16, 16, "879fe6243"),
    (12, 12, "879fe63"),
    (8, 8, "879ff"),
    (4, 4, "879"),
]


@pytest.mark.parametrize("level, expected_level, expected_token", S2_LEVELS_TO_TOKENS)
def test_s2_cell_id_from_lonlat_with_level(level, expected_level, expected_token):
    point = shapely.geometry.Point(-100.445833, 39.783333)
    s2cell = s2_cell_id(lon=point.x, lat=point.y, level=level)
    assert isinstance(s2cell, s2sphere.CellId)
    assert s2cell.level() == expected_level
    assert s2cell.to_token() == expected_token


@pytest.mark.parametrize("level, expected_level, expected_token", S2_LEVELS_TO_TOKENS)
def test_s2_cell_token_from_lonlat_with_level(level, expected_level, expected_token):
    point = shapely.geometry.Point(-100.44583297969389, 39.78333301429253)
    s2token = s2_cell_token(lon=point.x, lat=point.y, level=level)
    assert isinstance(s2token, str)
    assert s2token == expected_token
    # Test the accuracy of a round trip from a token back to lon, lat
    # https://s2geometry.io/resources/s2cell_statistics.html
    # http://wiki.gis.com/wiki/index.php/Decimal_degrees
    s2_point = s2_cell_to_lon_lat(s2token)
    if expected_level < 7:
        # forget it, the round trip is not accurate
        pass
    elif 7 <= expected_level < 10:
        # 0 decimal places has precision approx. 111 km
        # google s2 level 7 is approx. 80 km
        # google s2 level 9 is approx. 20 km
        assert point.x == pytest.approx(s2_point.lng, abs=1e-0)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-0)
    elif 10 <= expected_level < 13:
        # 1 decimal places has precision approx. 11.1 km
        # google s2 level 10 is approx. 10 km
        # google s2 level 12 is approx. 2 km
        assert point.x == pytest.approx(s2_point.lng, abs=1e-1)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-1)
    elif 13 <= expected_level < 17:
        # 2 decimal places has precision approx. 1.11 km
        # google s2 level 13 is approx. 1.2 km
        # google s2 level 16 is approx. 150 m
        assert point.x == pytest.approx(s2_point.lng, abs=1e-2)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-2)
    elif 17 <= expected_level < 20:
        # 3 decimal places has precision approx. 111 m
        # google s2 level 17 is approx. 80 m
        # google s2 level 19 is approx. 20 m
        assert point.x == pytest.approx(s2_point.lng, abs=1e-3)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-3)
    elif 20 <= expected_level < 27:
        # google s2 level 20 is approx. 10 m
        # google s2 level 26 is approx. 15 cm
        # 4 decimal places has precision approx. 11.1 m
        assert point.x == pytest.approx(s2_point.lng, abs=1e-4)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-4)
    elif 27 <= expected_level < 30:
        # google s2 level 27 is approx.  7 cm
        # google s2 level 30 is approx.  9 mm
        # 6 decimal places has precision approx. 11.1 cm
        assert point.x == pytest.approx(s2_point.lng, abs=1e-6)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-6)
    elif expected_level == 30:
        # google s2 level 30 is approx. 9 mm (why does this work?)
        # 8 decimal places has precision approx. 1.11 mm
        assert point.x == pytest.approx(s2_point.lng, abs=1e-8)
        assert point.y == pytest.approx(s2_point.lat, abs=1e-8)


@pytest.mark.parametrize("level, expected_level, expected_token", S2_LEVELS_TO_TOKENS)
def test_point_to_s2_cell_id_with_level(level, expected_level, expected_token):
    point = shapely.geometry.Point(-100.44583297969389, 39.78333301429253)
    s2cell = point_to_s2_cell_id(point=point, level=level)
    assert isinstance(s2cell, s2sphere.CellId)
    assert s2cell.level() == expected_level
    assert s2cell.to_token() == expected_token


@pytest.mark.parametrize("level, expected_level, expected_token", S2_LEVELS_TO_TOKENS)
def test_point_to_s2_cell_token_with_level(level, expected_level, expected_token):
    point = shapely.geometry.Point(-100.44583297969389, 39.78333301429253)
    s2token = point_to_s2_cell_token(point=point, level=level)
    assert isinstance(s2token, str)
    assert s2token == expected_token


def test_points_to_s2_cell_token_with_level():
    expected_level = 16
    expected_token = "879fe6243"
    point = shapely.geometry.Point(-100.44583297969389, 39.78333301429253)
    s2tokens = points_to_s2_cell_token(points=[point], level=expected_level)
    assert isinstance(s2tokens, Generator)
    s2token = next(s2tokens)
    assert isinstance(s2token, str)
    assert s2token == expected_token
