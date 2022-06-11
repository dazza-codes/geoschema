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
Test GeoJSON Schemas
====================

Test schemas for GeoJSON data.

"""

import geojson
import pytest
import shapely.geometry
from marshmallow import ValidationError

from geoschema.geojson_schemas import GeoJsonFeature
from geoschema.geojson_schemas import GeoJsonFeatureCollection
from geoschema.geojson_schemas import GeoJsonFeatureCollectionSchema
from geoschema.geojson_schemas import GeoJsonFeatureSchema
from geoschema.geojson_schemas import GeoJsonGeometryCollection
from geoschema.geojson_schemas import GeoJsonGeometryCollectionSchema
from geoschema.geojson_schemas import GeoJsonLineString
from geoschema.geojson_schemas import GeoJsonLineStringSchema
from geoschema.geojson_schemas import GeoJsonMultiLineString
from geoschema.geojson_schemas import GeoJsonMultiLineStringSchema
from geoschema.geojson_schemas import GeoJsonMultiPoint
from geoschema.geojson_schemas import GeoJsonMultiPointSchema
from geoschema.geojson_schemas import GeoJsonMultiPolygon
from geoschema.geojson_schemas import GeoJsonMultiPolygonSchema
from geoschema.geojson_schemas import GeoJsonPoint
from geoschema.geojson_schemas import GeoJsonPointSchema
from geoschema.geojson_schemas import GeoJsonPolygon
from geoschema.geojson_schemas import GeoJsonPolygonSchema


def test_geojson_point():
    x = -115.81
    y = 37.24
    point = geojson.Point((x, y))
    assert isinstance(point, geojson.geometry.Point)
    assert isinstance(point, dict)  # it is also a dict
    point_schema = GeoJsonPointSchema()
    geojson_point = point_schema.load(point)  # load a geojson dict
    assert isinstance(geojson_point, GeoJsonPoint)
    geojson_dump = geojson.dumps(point)
    geojson_point = point_schema.loads(geojson_dump)  # load a geojson string
    assert isinstance(geojson_point, GeoJsonPoint)
    serialized = geojson.dumps(geojson_point)
    assert (
        serialized == '{"type": "Point", '
        '"coordinates": [-115.81, 37.24], '
        '"bbox": [-115.81, 37.24, -115.81, 37.24]}'
    )
    assert geojson_point.x == pytest.approx(x, abs=1e-6)
    assert geojson_point.y == pytest.approx(y, abs=1e-6)
    shape = geojson_point.shape
    assert isinstance(shape, shapely.geometry.Point)
    assert geojson_point.bbox == list(shape.bounds)


def test_geojson_multi_point():
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
    assert (
        serialized == '{"type": "MultiPoint", '
        '"coordinates": [[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]], '
        '"bbox": [-157.97, 19.61, -155.52, 21.46]}'
    )
    shape = geojson_points.shape
    assert isinstance(shape, shapely.geometry.MultiPoint)
    assert geojson_points.bbox == list(shape.bounds)


def test_geojson_line_string():
    line_string = geojson.LineString([(8.919, 44.4074), (8.923, 44.4075)])
    assert isinstance(line_string, geojson.geometry.LineString)
    assert isinstance(line_string, dict)  # it is also a dict
    schema = GeoJsonLineStringSchema()
    geojson_line = schema.load(line_string)  # load a geojson dict
    assert isinstance(geojson_line, GeoJsonLineString)
    geojson_dump = geojson.dumps(line_string)
    geojson_line = schema.loads(geojson_dump)  # load a geojson string
    assert isinstance(geojson_line, GeoJsonLineString)
    serialized = geojson.dumps(geojson_line)
    assert (
        serialized == '{"type": "LineString", '
        '"coordinates": [[8.919, 44.4074], [8.923, 44.4075]], '
        '"bbox": [8.919, 44.4074, 8.923, 44.4075]}'
    )
    shape = geojson_line.shape
    assert isinstance(shape, shapely.geometry.LineString)
    assert geojson_line.bbox == list(shape.bounds)


def test_geojson_multi_line_string():
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
    assert (
        serialized == '{"type": "MultiLineString", '
        '"coordinates": [[[3.75, 9.25], [-130.95, 1.52]], [[23.15, -34.25], [-1.35, -4.65], [3.45, 77.95]]], '
        '"bbox": [-130.95, -34.25, 23.15, 77.95]}'
    )
    shape = geojson_lines.shape
    assert isinstance(shape, shapely.geometry.MultiLineString)
    assert geojson_lines.bbox == list(shape.bounds)


def test_geojson_polygon():
    # no hole within polygon
    # polygon = geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]])
    # # hole within polygon
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
    assert (
        serialized
        == '{"type": "Polygon", "coordinates": [[[2.38, 57.322], [23.194, -20.28], '
        "[-120.43, 19.15], [2.38, 57.322]], [[-5.21, 23.51], [15.21, -10.81], "
        '[-20.51, 1.51], [-5.21, 23.51]]], "bbox": [-120.43, -20.28, 23.194, '
        "57.322]}"
    )
    shape = geojson_polygon.shape
    assert isinstance(shape, shapely.geometry.Polygon)
    assert geojson_polygon.bbox == list(shape.bounds)


def test_geojson_multi_polygon():
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
    assert (
        serialized
        == '{"type": "MultiPolygon", "coordinates": [[[[3.78, 9.28], [-130.91, 1.52], [35.12, '
        "72.234], [3.78, 9.28]]], [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], "
        '[23.18, -34.29]]]], "bbox": [-130.91, -34.29, 35.12, 77.91]}'
    )
    shape = geojson_polygons.shape
    assert isinstance(shape, shapely.geometry.MultiPolygon)
    assert geojson_polygons.bbox == list(shape.bounds)


def test_geojson_geometry_collection():
    point = geojson.Point((-115.81, 37.24))
    points = geojson.MultiPoint([(-155.52, 19.61), (-156.22, 20.74), (-157.97, 21.46)])
    line = geojson.LineString([(-152.62, 51.21), (5.21, 10.69)])
    lines = geojson.MultiLineString(
        [
            [(3.75, 9.25), (-130.95, 1.52)],
            [(23.15, -34.25), (-1.35, -4.65), (3.45, 77.95)],
        ]
    )
    polygon = geojson.Polygon(
        [
            [(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)],
            [(-5.21, 23.51), (15.21, -10.81), (-20.51, 1.51), (-5.21, 23.51)],
        ]
    )
    polygons = geojson.MultiPolygon(
        [
            ([(3.78, 9.28), (-130.91, 1.52), (35.12, 72.234), (3.78, 9.28)],),
            ([(23.18, -34.29), (-1.31, -4.61), (3.41, 77.91), (23.18, -34.29)],),
        ]
    )
    geo_collection = geojson.GeometryCollection(
        [point, points, line, lines, polygon, polygons]
    )
    assert isinstance(geo_collection, geojson.geometry.GeometryCollection)
    assert isinstance(geo_collection, dict)  # it is also a dict
    schema = GeoJsonGeometryCollectionSchema()
    geojson_collection = schema.load(geo_collection)  # load a geojson dict
    assert isinstance(geojson_collection, GeoJsonGeometryCollection)
    geojson_dump = geojson.dumps(geo_collection)
    geojson_collection = schema.loads(geojson_dump)  # load a geojson string
    assert isinstance(geojson_collection, GeoJsonGeometryCollection)
    assert geojson_collection.type == "GeometryCollection"
    classes = [obj.__class__.__name__ for obj in geojson_collection.geometries]
    assert classes == [
        "GeoJsonPoint",
        "GeoJsonMultiPoint",
        "GeoJsonLineString",
        "GeoJsonMultiLineString",
        "GeoJsonPolygon",
        "GeoJsonMultiPolygon",
    ]
    serialized = geojson.dumps(geojson_collection)
    assert (
        serialized
        == '{"type": "GeometryCollection", "geometries": [{"type": "Point", "bbox": [-115.81, 37.24, -115.81, 37.24], "coordinates": [-115.81, 37.24]}, {"type": "MultiPoint", "bbox": [-157.97, 19.61, -155.52, 21.46], "coordinates": [[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]]}, {"type": "LineString", "bbox": [-152.62, 10.69, 5.21, 51.21], "coordinates": [[-152.62, 51.21], [5.21, 10.69]]}, {"type": "MultiLineString", "bbox": [-130.95, -34.25, 23.15, 77.95], "coordinates": [[[3.75, 9.25], [-130.95, 1.52]], [[23.15, -34.25], [-1.35, -4.65], [3.45, 77.95]]]}, {"type": "Polygon", "bbox": [-120.43, -20.28, 23.194, 57.322], "coordinates": [[[2.38, 57.322], [23.194, -20.28], [-120.43, 19.15], [2.38, 57.322]], [[-5.21, 23.51], [15.21, -10.81], [-20.51, 1.51], [-5.21, 23.51]]]}, {"type": "MultiPolygon", "bbox": [-130.91, -34.29, 35.12, 77.91], "coordinates": [[[[3.78, 9.28], [-130.91, 1.52], [35.12, 72.234], [3.78, 9.28]]], [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], [23.18, -34.29]]]]}], "bbox": [-157.97, -34.29, 35.12, 77.95]}'
    )
    shape = geojson_collection.shape
    assert isinstance(shape, shapely.geometry.GeometryCollection)
    assert geojson_collection.bbox == list(shape.bounds)

    # Also, the schema.dump and schema.dumps should work
    geometries_dict = schema.dump(geojson_collection)
    geometries_json = schema.dumps(geojson_collection)
    assert isinstance(geometries_dict, dict)
    assert isinstance(geometries_json, str)
    assert geometries_dict == {
        "bbox": [-157.97, -34.29, 35.12, 77.95],
        "geometries": [
            {
                "type": "Point",
                "coordinates": [-115.81, 37.24],
                "bbox": [-115.81, 37.24, -115.81, 37.24],
            },
            {
                "type": "MultiPoint",
                "coordinates": [[-155.52, 19.61], [-156.22, 20.74], [-157.97, 21.46]],
                "bbox": [-157.97, 19.61, -155.52, 21.46],
            },
            {
                "type": "LineString",
                "coordinates": [[-152.62, 51.21], [5.21, 10.69]],
                "bbox": [-152.62, 10.69, 5.21, 51.21],
            },
            {
                "type": "MultiLineString",
                "coordinates": [
                    [[3.75, 9.25], [-130.95, 1.52]],
                    [[23.15, -34.25], [-1.35, -4.65], [3.45, 77.95]],
                ],
                "bbox": [-130.95, -34.25, 23.15, 77.95],
            },
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [2.38, 57.322],
                        [23.194, -20.28],
                        [-120.43, 19.15],
                        [2.38, 57.322],
                    ],
                    [[-5.21, 23.51], [15.21, -10.81], [-20.51, 1.51], [-5.21, 23.51]],
                ],
                "bbox": [-120.43, -20.28, 23.194, 57.322],
            },
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[3.78, 9.28], [-130.91, 1.52], [35.12, 72.234], [3.78, 9.28]]],
                    [[[23.18, -34.29], [-1.31, -4.61], [3.41, 77.91], [23.18, -34.29]]],
                ],
                "bbox": [-130.91, -34.29, 35.12, 77.91],
            },
        ],
        "type": "GeometryCollection",
    }


def test_geojson_feature_schema(geojson_features):
    # use the marshmallow schema to validate the GeoJSON feature
    feature = geojson_features[0]
    schema = GeoJsonFeatureSchema()
    loaded = schema.load(feature)  # raises on validation failure
    assert isinstance(loaded, GeoJsonFeature)
    schema_dict = schema.dump(loaded)
    schema_json = schema.dumps(loaded)
    assert isinstance(schema_dict, dict)
    assert isinstance(schema_json, str)
    assert schema_dict == {
        "type": "Feature",
        "geometry": {
            "bbox": [-118.365379, 34.199669, -118.365379, 34.199669],
            "coordinates": [-118.365379, 34.199669],
            "type": "Point",
        },
        "properties": {
            "stid": "KBUR",
            "elevation": 728,
            "mnet_id": 1,
            "name": "Burbank - Bob Hope Airport",
            "acquired_at": "2020-05-11T20:55:00",
            "air_temp": 23.0,
            "relative_humidity": 46.78,
            "wind_gust": 9.26,
            "wind_speed": 3.6,
            "wind_direction": 200,
        },
    }
    # The same serialization must work with geojson
    feature_json = geojson.dumps(loaded)
    assert isinstance(feature_json, str)
    feature_dict = geojson.loads(feature_json)
    assert isinstance(feature_dict, dict)
    assert feature_dict == schema_dict
    # Test the shapely shape
    shape = loaded.shape
    assert isinstance(shape, shapely.geometry.Point)
    assert loaded.geometry.bbox == list(shape.bounds)


def test_geojson_feature_schema_failure():
    # use the marshmallow schema to validate the GeoJSON feature
    schema = GeoJsonFeatureSchema()
    with pytest.raises(ValidationError):
        # missing geometry should fail to validate
        invalid_feature = {"type": "Feature", "properties": {}}
        schema.load(invalid_feature)
    with pytest.raises(ValidationError):
        # malformed geometry should fail to validate
        invalid_feature = {"type": "Feature", "geometry": {}, "properties": {}}
        schema.load(invalid_feature)


def test_geojson_feature_collection_schema(geojson_feature_collection):
    # use the marshmallow schema to validate the GeoJSON feature collection
    schema = GeoJsonFeatureCollectionSchema()
    loaded = schema.load(geojson_feature_collection)
    assert isinstance(loaded, GeoJsonFeatureCollection)
    assert isinstance(loaded.features[0], GeoJsonFeature)
    schema_dict = schema.dump(loaded)
    schema_json = schema.dumps(loaded)
    assert isinstance(schema_dict, dict)
    assert isinstance(schema_json, str)
    assert schema_dict == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-118.365379, 34.199669],
                    "bbox": [-118.365379, 34.199669, -118.365379, 34.199669],
                },
                "properties": {
                    "stid": "KBUR",
                    "elevation": 728,
                    "mnet_id": 1,
                    "name": "Burbank - Bob Hope Airport",
                    "acquired_at": "2020-05-11T20:55:00",
                    "air_temp": 23.0,
                    "relative_humidity": 46.78,
                    "wind_gust": 9.26,
                    "wind_speed": 3.6,
                    "wind_direction": 200,
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-120.566673, 37.366669],
                    "bbox": [-120.566673, 37.366669, -120.566673, 37.366669],
                },
                "properties": {
                    "stid": "KMER",
                    "elevation": 187,
                    "mnet_id": 1,
                    "name": "Merced / Castle Air Force Base",
                    "acquired_at": "2020-05-11T20:45:00",
                    "air_temp": 29.0,
                    "relative_humidity": 10.55,
                    "wind_gust": 7.2,
                    "wind_speed": 0.0,
                    "wind_direction": 0,
                },
            },
        ],
    }
    # The same serialization must work with geojson
    features_json = geojson.dumps(loaded)
    assert isinstance(features_json, str)
    features_dict = geojson.loads(features_json)
    assert isinstance(features_dict, dict)
    assert features_dict == schema_dict
    # Test the shapely shapes
    shapes = loaded.shapes
    assert isinstance(shapes[0], shapely.geometry.Point)
    assert isinstance(shapes[1], shapely.geometry.Point)
