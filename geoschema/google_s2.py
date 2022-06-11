"""
Google s2 utilities
-------------------

"""

from functools import partial
from typing import Generator
from typing import Iterable
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Union

import s2sphere
import shapely.geometry


class S2LatLng(NamedTuple):
    lat: float
    lng: float


def lonlat_to_s2_lonlat(lon: float, lat: float) -> s2sphere.LatLng:
    """
    Map the lon,lat value to an :py:class:`s2sphere.LatLng`

    :param lon: a longitude value in degrees
    :param lat: a latitude value in degrees
    :return: an s2sphere.LatLng
    """
    return s2sphere.LatLng.from_degrees(lng=lon, lat=lat)


def point_to_s2_lonlat(point: shapely.geometry.Point) -> s2sphere.LatLng:
    """
    Map a Point(lon,lat) to an :py:class:`s2sphere.LatLng`

    :param point: a shapely point that is assumed to be in WGS84 and
        constructed with `Point(lon,lat)` (not `Point(lat,lon)`)
        values in degrees
    :return: an s2sphere.LatLng
    """
    return s2sphere.LatLng.from_degrees(lng=point.x, lat=point.y)


def s2_cell_covering(
    point1: s2sphere.LatLng,
    point2: s2sphere.LatLng,
    inner: bool = True,
    min_level: int = 0,
    max_level: int = s2sphere.CellId.MAX_LEVEL,
) -> List[s2sphere.CellId]:
    """
    Find all the S2CellId that cover the interior of a rectangle defined by
    the points, where ``point1`` is "top-left" and ``point2`` is "bottom-right".

    :param point1: a s2sphere.LatLng point in degrees
    :param point2: a s2sphere.LatLng point in degrees
    :param inner: use an inner region covering, defaults to True
    :param max_level: an S2 geometry level, defaults to the lowest level (0)
    :param min_level: an S2 geometry level, defaults to the highest level (30)
    :return: a list of s2 CellId covering the rectangle

    Using the default levels, the inner covering includes the cell
    center and most of the cell, but it excludes the cell vertices
    (corner points).  The inner covering isolates one GeoTIFF cell
    from another.  The return list can be used as a cell union, e.g.

    .. code-block::

        cover_cells = s2_cell_covering(p1, p2)
        cell_union = s2sphere.CellUnion(cover_cells)
        # the CellUnion is useful for spatial queries, or
        # a list of CellId can be extracted from it:
        cell_union.cell_ids() # -> List[s2sphere.CellId]

    .. seealso::
        http://s2geometry.io/devguide/s2cell_hierarchy
        https://s2geometry.io/devguide/examples/coverings
        https://s2sphere.readthedocs.io/en/latest/_modules/s2sphere/sphere.html#RegionCoverer
        https://s2sphere.readthedocs.io/en/latest/_modules/s2sphere/sphere.html#CellUnion

    """
    rect = s2sphere.LatLngRect.from_point_pair(point1, point2)
    region = s2sphere.RegionCoverer()
    region.min_level = min_level
    region.max_level = max_level
    if inner:
        cover_cells = region.get_interior_covering(rect)
    else:
        cover_cells = region.get_covering(rect)

    return [cell for cell in cover_cells]


def s2_cell_id(lon: float, lat: float, level: int = 30) -> s2sphere.CellId:
    """
    Map the lat, lon value to a Google S2CellId at the level required
    (it defaults to level 30 in the Google S2 system).

    :param lon: a longitude value in degrees
    :param lat: a latitude value in degrees
    :param level: a level in the cell hierarchy, see
    https://s2geometry.io/resources/s2cell_statistics.html
    :return: a google S2CellId at the (lon,lat) for level
    """
    latlng = s2sphere.LatLng.from_degrees(lng=lon, lat=lat)
    s2cell = s2sphere.CellId.from_lat_lng(latlng)
    if 0 <= level < s2cell.level():
        # https://s2sphere.readthedocs.io/en/latest/_modules/s2sphere/sphere.html#CellId.parent
        s2cell = s2cell.parent(level)
    return s2cell


def s2_cell_token(lon: float, lat: float, level: int = 30) -> str:
    """
    Map the lat, lon value to a Google S2CellId.id()
    at the level required (it defaults to level 30
    in the Google S2 system).

    :param lon: a longitude value in degrees
    :param lat: a latitude value in degrees
    :param level: a level in the cell hierarchy, see
    https://s2geometry.io/resources/s2cell_statistics.html
    :return: a google S2CellId token at the (lon,lat) for level
    """
    return s2_cell_id(lon=lon, lat=lat, level=level).to_token()


def s2_cell_to_lon_lat(cell_id: Union[s2sphere.CellId, int, str]) -> S2LatLng:
    """
    Map a Google S2CellId to lat, lon value.

    :param cell_id: a google S2CellId
    :return: a named tuple with p.lng and p.lat values in degrees
    """
    if isinstance(cell_id, s2sphere.CellId):
        s2cell = cell_id
    elif isinstance(cell_id, int):
        s2cell = s2sphere.CellId(cell_id)
    elif isinstance(cell_id, str):
        s2cell = s2sphere.CellId.from_token(cell_id)
    else:
        raise ValueError("Cannot parse s2sphere.CellId")
    lat_lng = s2cell.to_lat_lng()
    return S2LatLng(lng=lat_lng.lng().degrees, lat=lat_lng.lat().degrees)


def point_to_s2_cell_id(
    point: shapely.geometry.Point, level: int = 30
) -> s2sphere.CellId:
    """
    Map the lat, lon value to a Google S2CellId at the level required
    (it defaults to level 30 in the Google S2 system).

    :param point: a shapely point that is assumed to be in WGS84 and
        constructed with `Point(lon,lat)` (not `Point(lat,lon)`)
        values in degrees
    :param level: a level in the cell hierarchy, see
    https://s2geometry.io/resources/s2cell_statistics.html
    :return: a google S2CellId at the `Point(lon,lat)`
    """
    return s2_cell_id(lon=point.x, lat=point.y, level=level)


def point_to_s2_cell_token(point: shapely.geometry.Point, level: int = 30) -> str:
    """
    Map the lat, lon value to a Google S2CellId token

    :param point: a shapely point that is assumed to be in WGS84 and
        constructed with `Point(lon,lat)` (not `Point(lat,lon)`)
        values in degrees
    :param level: a level in the cell hierarchy, see
    https://s2geometry.io/resources/s2cell_statistics.html
    :return: a google S2CellId at the lat, lon
    """
    return s2_cell_token(lon=point.x, lat=point.y, level=level)


def points_to_s2_cell_token(
    points: Iterable[shapely.geometry.Point], level: int = 30
) -> Generator[str, None, None]:
    """
    Map a set of points to google s2 Cell IDs

    :param points: an array of shapely points that are assumed to be
        in WGS84 and constructed with `Point(lon,lat)` (not `Point(lat,lon)`)
        values in degrees
    :param level: a level in the cell hierarchy, see
    https://s2geometry.io/resources/s2cell_statistics.html
    :return: an iterator for google S2CellId tokens for each point
    """
    point_to_s2token = partial(point_to_s2_cell_token, level=level)
    return (point_to_s2token(p) for p in points)
