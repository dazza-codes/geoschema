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

"""
GeoJSON Schemas
===============

Use marshmallow schema to validate GeoJSON data, e.g.

.. code-block::

    from geoschema.geojson_schemas import GeoJsonFeature
    from geoschema.geojson_schemas import GeoJsonFeatureCollection
    from geoschema.geojson_schemas import GeoJsonFeatureCollectionSchema

    schema = GeoJsonFeatureCollectionSchema()
    geo_features = schema.load(geojson_feature_collection)  # raises on validation failure
    geo_feature = geo_features.features[0]
    assert isinstance(geo_features, GeoJsonFeatureCollection)
    assert isinstance(geo_feature, GeoJsonFeature)
    schema_dict = schema.dump(geo_features)
    schema_json = schema.dumps(geo_features)
    assert isinstance(schema_dict, dict)
    assert isinstance(schema_json, str)
    # Get the geometries as shapely shapes
    geo_features.shapes
    geo_feature.shape

See details below for all the geometry types and schemas.

"""

from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Union

import geojson
import shapely.geometry
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_load
from marshmallow import validate

from geoschema.logger import get_logger

LOGGER = get_logger()


@dataclass
class GeoJsonGeometry:
    """
    Any GeoJSON geometry in 2D coordinates

    This is a generic base class or type for all of the GeoJSON geometries.
    To effectively use inheritance with dataclasses, it is easier to use all
    optional attributes that are initialized with None.  All the inherited
    classes override these defaults.
    """

    type: str = None
    coordinates: List[float] = None
    bbox: List[float] = None

    @property
    def __geo_interface__(self) -> Dict:
        return self.to_dict()

    def to_dict(self) -> Dict:
        return {"type": self.type, "coordinates": self.coordinates, "bbox": self.bbox}


@dataclass
class GeoJsonPoint(GeoJsonGeometry):
    """
    A GeoJSON point in 2D coordinates

    The `bbox` for a point is always going to be [x, y, x, y].

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonPoint
        >>> geojson_point = GeoJsonPoint(**{"type": "Point", "coordinates": [-115.81, 37.24]})
        GeoJsonPoint(type='Point', coordinates=[-115.81, 37.24], bbox=None)
        >>> geojson_point.x
        -115.81
        >>> geojson_point.y
        37.24
        >>> geojson.dumps(geojson_point)
        '{"type": "Point", "coordinates": [-115.81, 37.24], "bbox": [-115.81, 37.24, -115.81, 37.24]}'
        >>> geojson_point.shape
        <shapely.geometry.point.Point object at 0x7f5d5db1e320>

    .. seealso::
        - https://geojson.org/schema/Point.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.2
    """

    type: str = "Point"
    coordinates: List[float] = None
    bbox: List[float] = None

    def __post_init__(self):
        self._shape = shapely.geometry.Point(self.x, self.y)
        self.bbox = list(self._shape.bounds)

    @property
    def x(self):
        return self.coordinates[0]

    @property
    def y(self):
        return self.coordinates[1]

    @property
    def shape(self) -> shapely.geometry.Point:
        return self._shape


class GeoJsonPointSchema(Schema):
    """
    A GeoJSON point schema in 2D coordinates

    .. code-block::

        import geojson
        from geoschema.geojson_schemas import GeoJsonPoint
        from geoschema.geojson_schemas import GeoJsonPointSchema

        point = geojson.Point((-115.81, 37.24))
        assert isinstance(point, geojson.geometry.Point)
        assert isinstance(point, dict)  # it is also a Dict
        geojson_dump = geojson.dumps(point)
        point_schema = GeoJsonPointSchema()
        geojson_point = point_schema.load(point)  # load a geojson dict
        assert isinstance(geojson_point, GeoJsonPoint)
        geojson_point = point_schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_point, GeoJsonPoint)
        serialized = geojson.dumps(geojson_point)

    .. seealso::
        - https://geojson.org/schema/Point.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.2
    """

    type = fields.Str(validate=validate.Equal("Point"), required=True)
    coordinates = fields.List(
        fields.Float(), validate=validate.Length(min=2, max=2), required=True
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonPoint:
        return GeoJsonPoint(**data)


@dataclass
class GeoJsonMultiPoint(GeoJsonGeometry):
    """
    A GeoJSON line string in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonMultiPoint

        >>> data = {"coordinates": [[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]], "type": "MultiPoint"}
        >>> geojson_points = GeoJsonMultiPoint(**data)
        >>> geojson_points
        GeoJsonMultiPoint(type='MultiPoint', coordinates=[[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]], bbox=[-157.97, 19.61, -155.52, 21.46])
        >>> geojson.dumps(geojson_points)
        '{"type": "MultiPoint", "coordinates": [[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]], "bbox": [-157.97, 19.61, -155.52, 21.46]}'
        >>> geojson_points.shape
        <shapely.geometry.multipoint.MultiPoint object at 0x7f87ce877470>

    .. seealso::
        - https://geojson.org/schema/MultiPoint.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.3
    """

    type: str = "MultiPoint"
    coordinates: List[List[float]] = None
    bbox: List[float] = None

    def __post_init__(self):
        self._shape = shapely.geometry.MultiPoint(self.coordinates)
        self.bbox = list(self._shape.bounds)

    @property
    def shape(self) -> shapely.geometry.MultiPoint:
        return self._shape


class GeoJsonMultiPointSchema(Schema):
    """
    A GeoJSON MultiPoint schema in 2D coordinates

    .. code-block::

        import geojson
        from geoschema.geojson_schemas import GeoJsonMultiPoint
        from geoschema.geojson_schemas import GeoJsonMultiPointSchema

        multi_point = geojson.MultiPoint(
            [(-155.52, 19.61), (-156.22, 20.74), (-157.97, 21.46)]
        )
        assert isinstance(multi_point, geojson.geometry.MultiPoint)
        assert isinstance(multi_point, dict)  # it is also a dict
        schema = GeoJsonMultiPointSchema()
        geojson_points = schema.load(multi_point)  # load a geojson dict
        assert isinstance(geojson_points, GeoJsonMultiPoint)
        geojson_dump = geojson.dumps(multi_point)
        geojson_points = schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_points, GeoJsonMultiPoint)
        serialized = geojson.dumps(geojson_points)

    .. seealso::
        - https://geojson.org/schema/MultiPoint.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.3
    """

    type = fields.Str(validate=validate.Equal("MultiPoint"), required=True)
    coordinates = fields.List(
        fields.List(fields.Float(), validate=validate.Length(min=2, max=2)),
        required=True,
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonMultiPoint:
        return GeoJsonMultiPoint(**data)


@dataclass
class GeoJsonLineString(GeoJsonGeometry):
    """
    A GeoJSON line string in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonLineString

        >>> data = {"type": "LineString", "coordinates": [[8.919, 44.4074], [8.923, 44.4075]]}
        >>> geojson_line = GeoJsonLineString(**data)
        >>> geojson_line
        GeoJsonLineString(type='LineString', coordinates=[[8.919, 44.4074], [8.923, 44.4075]], bbox=[8.919, 44.4074, 8.923, 44.4075])
        >>> geojson.dumps(geojson_line)
        '{"type": "LineString", "coordinates": [[8.919, 44.4074], [8.923, 44.4075]], "bbox": [8.919, 44.4074, 8.923, 44.4075]}'
        >>> geojson_line.shape
        <shapely.geometry.linestring.LineString object at 0x7f3a5b344780>

    .. seealso::
        - https://geojson.org/schema/LineString.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.4
    """

    type: str = "LineString"
    coordinates: List[List[float]] = None
    bbox: List[float] = None

    def __post_init__(self):
        self._shape = shapely.geometry.LineString(self.coordinates)
        self.bbox = list(self._shape.bounds)

    @property
    def shape(self) -> shapely.geometry.LineString:
        return self._shape


class GeoJsonLineStringSchema(Schema):
    """
    A GeoJSON line string schema in 2D coordinates

    .. code-block::

        import geojson
        from geoschema.geojson_schemas import GeoJsonLineString
        from geoschema.geojson_schemas import GeoJsonLineStringSchema

        line_string = geojson.LineString([(8.919, 44.4074), (8.923, 44.4075)])
        assert isinstance(line_string, geojson.geometry.LineString)
        assert isinstance(line_string, dict)  # it is also a dict
        geojson_dump = geojson.dumps(line_string)
        schema = GeoJsonLineStringSchema()
        geojson_line = schema.load(line_string)  # load a geojson dict
        assert isinstance(geojson_line, GeoJsonLineString)
        geojson_line = schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_line, GeoJsonLineString)
        serialized = geojson.dumps(geojson_line)

    .. seealso::
        - https://geojson.org/schema/LineString.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.4
    """

    type = fields.Str(validate=validate.Equal("LineString"), required=True)
    coordinates = fields.List(
        fields.List(fields.Float(), validate=validate.Length(min=2, max=2)),
        validate=validate.Length(min=2),
        required=True,
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonLineString:
        return GeoJsonLineString(**data)


@dataclass
class GeoJsonMultiLineString(GeoJsonGeometry):
    """
    A GeoJSON MultiLineString in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonMultiLineString

        >>> data = {"type": "MultiLineString", "coordinates": [[8.919, 44.4074], [8.923, 44.4075]]}
        >>> geojson_line = GeoJsonMultiLineString(**data)
        >>> geojson_line
        GeoJsonMultiLineString(type='MultiLineString', coordinates=[[8.919, 44.4074], [8.923, 44.4075]], bbox=[8.919, 44.4074, 8.923, 44.4075])
        >>> geojson.dumps(geojson_line)
        '{"type": "MultiLineString", "coordinates": [[8.919, 44.4074], [8.923, 44.4075]], "bbox": [8.919, 44.4074, 8.923, 44.4075]}'
        >>> geojson_line.shape
        <shapely.geometry.linestring.MultiLineString object at 0x7f3a5b344780>

    .. seealso::
        - https://geojson.org/schema/MultiLineString.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.5
    """

    type: str = "MultiLineString"
    coordinates: List[List[List[float]]] = None
    bbox: List[float] = None

    def __post_init__(self):
        self._shape = shapely.geometry.MultiLineString(self.coordinates)
        self.bbox = list(self._shape.bounds)

    @property
    def shape(self) -> shapely.geometry.MultiLineString:
        return self._shape


class GeoJsonMultiLineStringSchema(Schema):
    """
    A MultiLineString composed of a list of line strings in 2D coordinates

    .. code-block::

        multi_line = geojson.MultiLineString(
            [
                [(3.75, 9.25), (-130.95, 1.52)],
                [(23.15, -34.25), (-1.35, -4.65), (3.45, 77.95)],
            ]
        )
        assert isinstance(multi_line, geojson.geometry.MultiLineString)
        assert isinstance(multi_line, dict)  # it is also a dict
        schema = GeoJsonMultiLineStringSchema()
        geojson_lines = schema.load(multi_line)  # load a geojson dict
        assert isinstance(geojson_lines, GeoJsonMultiLineString)
        geojson_dump = geojson.dumps(multi_line)
        geojson_lines = schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_lines, GeoJsonMultiLineString)
        serialized = geojson.dumps(geojson_lines)

    .. seealso::
        - https://geojson.org/schema/MultiLineString.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.5
    """

    type = fields.Str(validate=validate.Equal("MultiLineString"), required=True)
    coordinates = fields.List(
        fields.List(
            fields.List(fields.Float(), validate=validate.Length(min=2, max=2)),
            validate=validate.Length(min=2),
        ),
        required=True,
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonMultiLineString:
        return GeoJsonMultiLineString(**data)


@dataclass
class GeoJsonPolygon(GeoJsonGeometry):
    """
    A GeoJSON Polygon in 2D coordinates

    - For type "Polygon", the "coordinates" member MUST be an array of
      linear ring coordinate arrays.
    - For Polygons with more than one of these rings, the first MUST be
      the exterior ring, and any others MUST be interior rings.  The
      exterior ring bounds the surface, and the interior rings (if
      present) bound holes within the surface.

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonPolygon

        >>> data = {"type": "Polygon", "coordinates": [[[2.38, 57.322], [23.194, -20.28], [-120.43, 19.15], [2.38, 57.322]], [[-5.21, 23.51], [15.21, -10.81], [-20.51, 1.51], [-5.21, 23.51]]]}
        >>> geojson_polygon = GeoJsonPolygon(**data)
        >>> geojson_polygon
        GeoJsonPolygon(type='Polygon', coordinates=[[[2.38, 57.322], [23.194, -20.28], [-120.43, 19.15], [2.38, 57.322]], [[-5.21, 23.51], [15.21, -10.81], [-20.51, 1.51], [-5.21, 23.51]]], bbox=[-120.43, -20.28, 23.194, 57.322])
        >>> geojson.dumps(geojson_polygon)
        '{"type": "Polygon", "coordinates": [[[2.38, 57.322], [23.194, -20.28], [-120.43, 19.15], [2.38, 57.322]], [[-5.21, 23.51], [15.21, -10.81], [-20.51, 1.51], [-5.21, 23.51]]], "bbox": [-120.43, -20.28, 23.194, 57.322]}'
        >>> geojson_polygon.shape
        <shapely.geometry.polygon.Polygon object at 0x7fb653dbce10>

    .. seealso::
        - https://geojson.org/schema/Polygon.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.6
    """

    type: str = "Polygon"
    coordinates: List[List[List[float]]] = None
    bbox: List[float] = None

    def __post_init__(self):
        # the first linear ring of the coordinates must be the exterior ring
        # and the rest of them must be one or more interior rings
        self._shape = shapely.geometry.Polygon(
            self.coordinates[0], self.coordinates[1:]
        )
        self.bbox = list(self._shape.bounds)

    @property
    def shape(self) -> shapely.geometry.Polygon:
        return self._shape


class GeoJsonPolygonSchema(Schema):
    """
    A GeoJSON Polygon schema in 2D coordinates

    .. code-block::

        import geojson
        from geoschema.geojson_schemas import GeoJsonPolygon
        from geoschema.geojson_schemas import GeoJsonPolygonSchema

        # hole within polygon
        polygon = geojson.Polygon(
            [
                [(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)],
                [(-5.21, 23.51), (15.21, -10.81), (-20.51, 1.51), (-5.21, 23.51)],
            ]
        )
        assert isinstance(polygon, geojson.geometry.Polygon)
        assert isinstance(polygon, dict)  # it is also a dict
        polygon_schema = GeoJsonPolygonSchema()
        geojson_polygon = polygon_schema.load(polygon)  # load a geojson dict
        assert isinstance(geojson_polygon, GeoJsonPolygon)
        geojson_dump = geojson.dumps(polygon)
        geojson_polygon = polygon_schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_polygon, GeoJsonPolygon)
        serialized = geojson.dumps(geojson_polygon)

    .. seealso::
        - https://geojson.org/schema/Polygon.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.6
    """

    type = fields.Str(validate=validate.Equal("Polygon"), required=True)
    coordinates = fields.List(
        fields.List(
            fields.List(fields.Float(), validate=validate.Length(min=2, max=2)),
            validate=validate.Length(min=4),
        ),
        required=True,
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonPolygon:
        return GeoJsonPolygon(**data)


@dataclass
class GeoJsonMultiPolygon(GeoJsonGeometry):
    """
    A GeoJSON MultiPolygon in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonMultiPolygon

        >>> data = {"type": "MultiPolygon", "coordinates": [[[[3.78, 9.28], [-130.91, 1.52], [35.12, 72.234], [3.78, 9.28]]], [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], [23.18, -34.29]]]]}
        >>> geojson_polygons = GeoJsonMultiPolygon(**data)
        >>> geojson_polygons
        GeoJsonMultiPolygon(type='MultiPolygon', coordinates=[[[[3.78, 9.28], [-130.91, 1.52], [35.12, 72.234], [3.78, 9.28]]], [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], [23.18, -34.29]]]], bbox=[-130.91, -34.29, 35.12, 77.91])
        >>> geojson.dumps(geojson_polygons)
        '{"type": "MultiPolygon", "coordinates": [[[[3.78, 9.28], [-130.91, 1.52], [35.12, 72.234], [3.78, 9.28]]], [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], [23.18, -34.29]]]], "bbox": [-130.91, -34.29, 35.12, 77.91]}'
        >>> geojson_polygons.shape
        <shapely.geometry.multipolygon.MultiPolygon object at 0x7fe6a0337828>

    .. seealso::
        - https://geojson.org/schema/MultiPolygon.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.7
    """

    type: str = "MultiPolygon"
    coordinates: List[List[List[List[float]]]] = None
    bbox: List[float] = None

    def __post_init__(self):
        polygons = [
            shapely.geometry.Polygon(polygon[0], polygon[1:])
            for polygon in self.coordinates
        ]
        self._shape = shapely.geometry.MultiPolygon(polygons)
        self.bbox = list(self._shape.bounds)

    @property
    def shape(self) -> shapely.geometry.MultiPolygon:
        return self._shape


class GeoJsonMultiPolygonSchema(Schema):
    """
    A GeoJSON MultiPolygon schema in 2D coordinates

    .. code-block::

        import geojson
        from geoschema.geojson_schemas import GeoJsonMultiPolygon
        from geoschema.geojson_schemas import GeoJsonMultiPolygonSchema

        polygons = geojson.MultiPolygon(
            [
                ([(3.78, 9.28), (-130.91, 1.52), (35.12, 72.234), (3.78, 9.28)],),
                ([(23.18, -34.29), (-1.31, -4.61), (3.41, 77.91), (23.18, -34.29)],),
            ]
        )
        assert isinstance(polygons, geojson.geometry.MultiPolygon)
        assert isinstance(polygons, dict)  # it is also a dict
        polygon_schema = GeoJsonMultiPolygonSchema()
        geojson_polygons = polygon_schema.load(polygons)  # load a geojson dict
        assert isinstance(geojson_polygons, GeoJsonMultiPolygon)
        geojson_dump = geojson.dumps(polygons)
        geojson_polygons = polygon_schema.loads(geojson_dump)  # load a geojson string
        assert isinstance(geojson_polygons, GeoJsonMultiPolygon)
        serialized = geojson.dumps(geojson_polygons)

    .. seealso::
        - https://geojson.org/schema/MultiPolygon.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.7
    """

    type = fields.Str(validate=validate.Equal("MultiPolygon"), required=True)
    coordinates = fields.List(
        fields.List(
            fields.List(
                fields.List(fields.Float(), validate=validate.Length(min=2, max=2)),
                validate=validate.Length(min=4),
            ),
        ),
        required=True,
    )
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonMultiPolygon:
        return GeoJsonMultiPolygon(**data)


GEOMETRY_SCHEMAS = [
    GeoJsonPointSchema(),
    GeoJsonLineStringSchema(),
    GeoJsonPolygonSchema(),
    GeoJsonMultiPointSchema(),
    GeoJsonMultiLineStringSchema(),
    GeoJsonMultiPolygonSchema(),
]

GEOMETRY_TYPES = [
    GeoJsonPoint,
    GeoJsonLineString,
    GeoJsonPolygon,
    GeoJsonMultiPoint,
    GeoJsonMultiLineString,
    GeoJsonMultiPolygon,
]


def parse_geometry(
    geometry: Dict,
) -> Union[
    None,
    GeoJsonGeometry,
    GeoJsonPoint,
    GeoJsonMultiPoint,
    GeoJsonLineString,
    GeoJsonMultiLineString,
    GeoJsonPolygon,
    GeoJsonMultiPolygon,
]:
    if isinstance(geometry, GeoJsonGeometry):
        return geometry

    if isinstance(geometry, str):
        geometry = geojson.loads(geometry)

    if isinstance(geometry, Dict):
        for schema in GEOMETRY_SCHEMAS:
            try:
                return schema.load(geometry)
            except ValidationError:
                pass

    LOGGER.warning("Unknown geometry: %s", geometry)


def parse_geometries(
    geometries: List,
) -> List[
    Union[
        None,
        GeoJsonGeometry,
        GeoJsonPoint,
        GeoJsonMultiPoint,
        GeoJsonLineString,
        GeoJsonMultiLineString,
        GeoJsonPolygon,
        GeoJsonMultiPolygon,
    ]
]:
    shapes = map(parse_geometry, geometries)
    return [shape for shape in shapes if shape is not None]


class GeoJsonGeometryField(fields.Field):
    """
    A GeoJSON Geometry Field
    """

    def _serialize(self, value, attr, obj, **kwargs) -> Dict:
        """
        Serialize a GeoJSON Geometry Field into a GeoJSON Dict

        :param value: value is assumed to be a GeoJSON Geometry Field
        :param attr:
        :param obj:
        :param kwargs:
        :return: GeoJSON Dict representation for the Geometry Field
        """
        if isinstance(value, GeoJsonGeometry):
            return value.to_dict()
        return geojson.loads(geojson.dumps(value))

    def _deserialize(
        self, value, attr, data, **kwargs
    ) -> Union[
        GeoJsonPoint,
        GeoJsonMultiPoint,
        GeoJsonLineString,
        GeoJsonMultiLineString,
        GeoJsonPolygon,
        GeoJsonMultiPolygon,
    ]:
        """
        Parse a GeoJSON Geometry string into a GeoJSON Geometry Field

        :param value: value is assumed to be a GeoJSON Geometry string
        :param attr:
        :param obj:
        :param kwargs:
        :return: any one of the GeoJSON Geometry Field types
        """
        try:
            geometry = parse_geometry(value)
            if geometry is None:
                raise ValueError("Unknown geometry data.")
            return geometry
        except ValueError as error:
            raise ValidationError("Unknown geometry data.") from error


@dataclass
class GeoJsonGeometryCollection:
    """
    A GeoJSON GeometryCollection in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonGeometryCollection

        >>> data = {
             "type": "GeometryCollection",
             "geometries": [
                  {
                      "type": "Point",
                      "coordinates": [-115.81, 37.24]
                  },
                  {
                      "type": "LineString",
                      "coordinates": [[-152.62, 51.21], [5.21, 10.69]]
                  }
            ]
        }
        >>> geo_collection = GeoJsonGeometryCollection(**data)
        >>> assert isinstance(geo_collection, GeoJsonGeometryCollection)
        >>> geojson.dumps(geo_collection)
        '{"type": "GeometryCollection", "geometries": [{"type": "Point", "bbox": [-115.81, 37.24, -115.81, 37.24], "coordinates": [-115.81, 37.24]}, {"type": "LineString", "bbox": [-152.62, 10.69, 5.21, 51.21], "coordinates": [[-152.62, 51.21], [5.21, 10.69]]}], "bbox": [-152.62, 10.69, 5.21, 51.21]}'
        >>> geo_collection.shape
        <shapely.geometry.collection.GeometryCollection object at 0x7ff35d2e7278>


    .. seealso::
        - https://geojson.org/schema/GeometryCollection.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.8
    """

    type: str = "GeometryCollection"
    geometries: List[
        Union[
            str,
            GeoJsonGeometry,
            GeoJsonPoint,
            GeoJsonMultiPoint,
            GeoJsonLineString,
            GeoJsonMultiLineString,
            GeoJsonPolygon,
            GeoJsonMultiPolygon,
        ]
    ] = None
    bbox: List[float] = None

    def __post_init__(self):
        self.geometries = parse_geometries(self.geometries)
        shapes = [s.shape for s in self.geometries]
        self._shape = shapely.geometry.GeometryCollection(shapes)
        self.bbox = list(self._shape.bounds)

    @property
    def __geo_interface__(self) -> Dict:
        return self.to_dict()

    @property
    def shape(self) -> shapely.geometry.GeometryCollection:
        return self._shape

    def to_dict(self) -> Dict:
        return {"type": self.type, "geometries": self.geometries, "bbox": self.bbox}


class GeoJsonGeometryCollectionSchema(Schema):
    """
    A GeoJSON GeometryCollection schema in 2D coordinates

    .. code-block::

        >>> import geojson
        >>> from geoschema.geojson_schemas import GeoJsonGeometryCollection
        >>> from geoschema.geojson_schemas import GeoJsonGeometryCollectionSchema

        >>> data = {
             "type": "GeometryCollection",
             "geometries": [
                  {
                      "type": "Point",
                      "coordinates": [-115.81, 37.24]
                  },
                  {
                      "type": "LineString",
                      "coordinates": [[-152.62, 51.21], [5.21, 10.69]]
                  }
            ]
        }
        >>> schema = GeoJsonGeometryCollectionSchema()
        >>> geo_collection = schema.load(geo_collection)  # load a geojson dict
        >>> assert isinstance(geo_collection, GeoJsonGeometryCollection)
        >>> geojson.dumps(geo_collection)
        '{"type": "GeometryCollection", "geometries": [{"type": "Point", "bbox": [-115.81, 37.24, -115.81, 37.24], "coordinates": [-115.81, 37.24]}, {"type": "LineString", "bbox": [-152.62, 10.69, 5.21, 51.21], "coordinates": [[-152.62, 51.21], [5.21, 10.69]]}], "bbox": [-152.62, 10.69, 5.21, 51.21]}'


    .. seealso::
        - https://geojson.org/schema/GeometryCollection.json
        - https://tools.ietf.org/html/rfc7946#section-3.1.8
    """

    type = fields.Str(validate=validate.Equal("GeometryCollection"), required=True)
    # geometries = fields.List(fields.Dict(), many=True, required=True)
    geometries = fields.List(GeoJsonGeometryField(), required=True)
    bbox = fields.List(
        fields.Float(), validate=validate.Length(min=4), load_default=None
    )

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonGeometryCollection:
        return GeoJsonGeometryCollection(**data)


@dataclass
class GeoJsonFeature:
    type: str = "Feature"
    geometry: Union[
        Dict,
        GeoJsonPoint,
        GeoJsonMultiPoint,
        GeoJsonLineString,
        GeoJsonMultiLineString,
        GeoJsonPolygon,
        GeoJsonMultiPolygon,
    ] = None
    properties: Dict = None

    def __post_init__(self):
        self.geometry = parse_geometry(self.geometry)
        self.bbox = list(self.geometry.shape.bounds)

    @property
    def __geo_interface__(self) -> Dict:
        return {
            "type": self.type,
            "geometry": self.geometry,
            "properties": self.properties,
        }

    @property
    def shape(
        self,
    ) -> Union[
        shapely.geometry.Point,
        shapely.geometry.MultiPoint,
        shapely.geometry.LineString,
        shapely.geometry.MultiLineString,
        shapely.geometry.Polygon,
        shapely.geometry.MultiPolygon,
    ]:
        return self.geometry.shape


class GeoJsonFeatureSchema(Schema):
    id = fields.Str()  # optional
    type = fields.Str(required=True, validate=validate.Equal("Feature"))
    # geometry = fields.Dict(required=True)
    geometry = GeoJsonGeometryField(required=True)
    properties = fields.Dict(required=True)

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonFeature:
        return GeoJsonFeature(**data)


@dataclass
class GeoJsonFeatureCollection:
    type: str = "FeatureCollection"
    features: List[Union[Dict, GeoJsonFeature]] = None

    @property
    def __geo_interface__(self) -> Dict:
        return self.to_dict()

    @property
    def shapes(
        self,
    ) -> List[
        Union[
            shapely.geometry.Point,
            shapely.geometry.MultiPoint,
            shapely.geometry.LineString,
            shapely.geometry.MultiLineString,
            shapely.geometry.Polygon,
            shapely.geometry.MultiPolygon,
        ]
    ]:
        return [f.geometry.shape for f in self.features]

    def to_dict(self) -> Dict:
        return {"type": self.type, "features": self.features}


class GeoJsonFeatureCollectionSchema(Schema):
    type = fields.Str(required=True, validate=validate.Equal("FeatureCollection"))
    features = fields.Nested(GeoJsonFeatureSchema(many=True), required=True)

    @post_load
    def make_obj(self, data, **kwargs) -> GeoJsonFeatureCollection:
        return GeoJsonFeatureCollection(**data)
