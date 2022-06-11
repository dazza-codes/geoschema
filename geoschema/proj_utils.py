# Copyright 2019-2022 Darren Weber
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List
from typing import Optional
from typing import Tuple

import pyproj
import shapely.geometry
from pydantic import BaseModel
from pydantic import Field
from pydantic import root_validator
from pydantic import validator

LONLAT4326_PROJ: pyproj.Proj = pyproj.Proj("EPSG:4326")

LONLAT4326_PYPROJ_CRS: pyproj.CRS = pyproj.CRS.from_epsg(4326)

LONLAT4326_BOUNDS_POLYGON: shapely.geometry.Polygon = (
    shapely.geometry.Polygon.from_bounds(xmin=-180.0, ymin=-90.0, xmax=180.0, ymax=90.0)
)


def pyproj_epsg(epsg: int) -> pyproj.CRS:
    """
    Get a pyproj CRS for an EPSG identifier

    .. code-block::

        proj_crs4326 = pyproj_epsg(4326)

    :param epsg: an EPSG integer identifier
    :return: a pyproj CRS for the EPSG
    """
    return pyproj.CRS.from_epsg(epsg)


def pyproj_lonlat_to_xy_transformer(src_crs: pyproj.CRS) -> pyproj.Transformer:
    """
    Create a pyproj.Transformer for (lon,lat) -> (x,y) projection;
    the transformer is created with `always_xy=True` to autocorrect for
    any CRS axis flips; it allows always using (lon,lat) -> (x,y) for
    any source CRS.

    .. code-block::

        transformer = pyproj_lonlat_to_xy_transformer(src.crs)
        x, y = transformer.transform(lon, lat)  # in that order

    :param src_crs: source CRS as a pyproj.CRS
    :return: a pyproj.Transformer
    """
    # Note: this function is used to encapsulate the lon,lat projections
    #       to encapsulate use of pyproj and other CRS libraries and to
    #       isolate changes in those libraries to this function.
    return pyproj.Transformer.from_crs(
        crs_from=LONLAT4326_PYPROJ_CRS, crs_to=src_crs, always_xy=True
    )


def pyproj_xy_to_lonlat_transformer(src_crs: pyproj.CRS) -> pyproj.Transformer:
    """
    Create a pyproj.Transformer for (x,y) -> (lon,lat) raster projection;
    the transformer is created with `always_xy=True` to autocorrect for
    any CRS axis flips; it allows always using (x,y) -> (lon,lat) for
    any source CRS.

    .. code-block::

        transformer = pyproj_xy_to_lonlat_transformer(src.crs)
        lon, lat = transformer.transform(x, y)  # in that order

    :param src_crs: source CRS as a rasterio.crs.CRS or pyproj.CRS
    :return: a pyproj.Transformer
    """
    # Note: this function is used to encapsulate the lon,lat projections
    #       to encapsulate use of pyproj and other CRS libraries and to
    #       isolate changes in those libraries to this function.
    return pyproj.Transformer.from_crs(
        crs_from=src_crs, crs_to=LONLAT4326_PYPROJ_CRS, always_xy=True
    )


def pyproj_lonlat_to_xy(
    src_crs: pyproj.CRS, lon: float, lat: float
) -> Tuple[float, float]:
    """
    Project a lon,lat location to an x,y
    (lon, lat) -> (x, y) projected space

    :param src_crs: source CRS as a pyproj.CRS
    :param lon: longitude
    :param lat: latitude
    :return: x, y in the source CRS
    """
    proj = pyproj_lonlat_to_xy_transformer(src_crs)
    x, y = proj.transform(lon, lat)
    return x, y


def pyproj_xy_to_lonlat(
    src_crs: pyproj.CRS, x: float, y: float
) -> Tuple[float, float]:
    """
    Project  a raster x,y to a lon,lat location
    (x, y) -> (lon, lat)

    :param src_crs: source CRS as a pyproj.CRS
    :param x: location in source CRS
    :param y: location in source CRS
    :return: lon,lat location
    """
    # Note: this function is used to encapsulate the lon,lat projections
    #       to encapsulate use of pyproj and other CRS libraries and to
    #       isolate changes in those libraries to this function.
    transformer = pyproj_xy_to_lonlat_transformer(src_crs)
    lon, lat = transformer.transform(x, y)  # in that order
    return lon, lat


def valid_lonlat(
    lon: float, lat: float, wrap: bool = False
) -> Optional[shapely.geometry.Point]:
    """
    This validates a lat and lon point can be located
    in the bounds of the WGS84 CRS

    :param lon: a longitude value
    :param lat: a latitude value
    :param wrap: wrap any longitude value within [-180, 180)
    :return: shapely.geometry.Point(lon, lat) if valid, None otherwise
    """
    if wrap:
        # Put the longitude in the range of [0,360):
        lon %= 360
        # Put the longitude in the range of [-180,180):
        if lon >= 180:
            lon -= 360
    point = shapely.geometry.Point(lon, lat)
    if LONLAT4326_BOUNDS_POLYGON.intersects(point):
        return point


def validate_latitude(lat: float) -> float:
    if -90 <= lat <= 90:
        return lat
    raise ValueError("latitude must be [-90.0, 90.0]")


def validate_longitude(lon: float) -> float:
    if -180 <= lon <= 180:
        return lon
    raise ValueError("longitude must be [-180.0, 180.0]")


def wrap_longitude(lon: float) -> float:
    """
    Modify the longitude by wrapping it within [-180, 180].
    """
    # Put the longitude in the range of [0,360):
    lon %= 360
    # Put the longitude in the range of [-180,180]:
    if lon > 180:
        lon -= 360
    return lon


class LonLat(BaseModel):
    """Coordinates for longitude and latitude (in degrees)

    The longitude value must be within [-180, 180).
    """

    latitude: float = Field(
        description="A WGS84 latitude (in degrees)",
        ge=-90,
        le=90,
    )
    longitude: float = Field(
        description="A WGS84 longitude (in degrees)",
        ge=-180,
        le=180,
    )

    class Config:
        schema_extra = {"example": {"longitude": -122.395556, "latitude": 37.793871}}
        frozen = True

    @property
    def lon(self) -> float:
        return self.longitude

    @property
    def lat(self) -> float:
        return self.latitude

    @property
    def coordinates(self) -> List[float]:
        """The [longitude, latitude] coordinates"""
        return [self.longitude, self.latitude]

    @property
    def point(self) -> shapely.geometry.Point:
        """A shapely.geometry.Point(longitude, latitude)"""
        return shapely.geometry.Point(self.longitude, self.latitude)

    @property
    def wkt(self) -> str:
        return self.point.wkt

    def is_valid(self) -> bool:
        """
        :return: True if the (longitude, latitude) is in WGS84 bounds
        """
        return LONLAT4326_BOUNDS_POLYGON.intersects(self.point)

    @validator("latitude")
    def validate_latitude(cls, value):
        return validate_latitude(value)

    @validator("longitude")
    def validate_longitude(cls, value):
        return validate_longitude(value)

    @root_validator
    def lonlat_validator(cls, values):
        lon = values.get("longitude")
        lat = values.get("latitude")
        if lon and lat:
            point = valid_lonlat(lon, lat, wrap=False)
            if point is None:
                raise ValueError("(longitude, latitude) are outside WGS84")
        return values
