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
GeoJSON Utilities
=================

Utilities to manipulate GeoJSON data

.. seealso::
    - GeoJSON Format: https://tools.ietf.org/html/rfc7946
    - GeoJSON json-schema: https://github.com/geojson/schema
    - python library: https://github.com/jazzband/geojson

"""

import csv
import json
from pathlib import Path
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import geojson
import geopandas as gpd
import pandas as pd
import shapely.geometry

from geoschema.google_s2 import points_to_s2_cell_token
from geoschema.proj_utils import LONLAT4326_PYPROJ_CRS
from geoschema.proj_utils import valid_lonlat
from geoschema.uuid_utils import get_uuids

from geoschema.logger import get_logger

LOGGER = get_logger()


def geojson_from_gdf(gdf: gpd.GeoDataFrame) -> Dict:
    feature_collection = geojson.loads(gdf.to_json())
    assert len(feature_collection["features"]) == len(gdf)
    return feature_collection


def df_with_uuid(df: pd.DataFrame):
    LOGGER.info("Adding UUIDs to DataFrame")
    uuids = get_uuids(len(df))
    df["uuid"] = pd.Series(uuids, dtype="string")


def gdf_with_uuid(gdf: gpd.GeoDataFrame):
    """
    Add a 'uuid' column
    :param gdf: a geopandas.GeoDataFrame
    """
    LOGGER.info("Adding UUIDs to GeoDataFrame")
    uuids = get_uuids(len(gdf))
    gdf["uuid"] = pd.Series(uuids, dtype="string")


def gdf_with_google_s2(gdf: gpd.GeoDataFrame):
    """
    Add a 's2_cell_id' column for a Google s2 cell ID from the geometry,
    assuming that the geometry is in WGS84 (lon, lat) points
    :param gdf: a geopandas.GeoDataFrame
    """
    LOGGER.info("Adding google S2 CellId to GeoDataFrame")
    s2_cells = points_to_s2_cell_token(points=gdf.geometry)
    gdf["s2_cell_id"] = pd.Series(s2_cells, dtype="string")


def gdf_validate_lonlat_points(gdf: gpd.GeoDataFrame, wrap: bool = False) -> bool:
    """
    Validate that a GeoDataFrame has a CRS in EPSG:4326 and that
    all the geometry shapes are points with (lon,lat) values

    :param gdf: a geopandas.GeoDataFrame
    :param wrap: wrap any longitude value within [-180, 180)
    """
    if not LONLAT4326_PYPROJ_CRS.is_exact_same(gdf.crs):
        LOGGER.error("CRS (%s) is not exact same as WGS84 EPSG:4326", gdf.crs)
        return False
    for p in gdf.geometry:
        assert isinstance(p, shapely.geometry.Point)
        if valid_lonlat(p.x, p.y, wrap) is None:
            LOGGER.error("POINT (%s) is not in WGS84 bounds", p)
            return False
    return True


def gdf_from_csv_file(
    csv_file: Union[Path, str],
    lon_field: str = "longitude",
    lat_field: str = "latitude",
    add_uuid: bool = True,
    add_s2: bool = True,
) -> gpd.GeoDataFrame:
    """
    Read a CSV file that contains WGS84 longitude and latitude
    columns for point geometries

    .. seealso::
        - https://geopandas.org/gallery/create_geopandas_from_pandas.html

    :param csv_file: a string or Path to a CSV file
    :param lon_field: the name of the longitude column
    :param lat_field: the name of the latitude column
    :param add_s2: add google s2 cell ID to each point
    :param add_uuid: add a UUID to each point
    :return: a geopandas.GeoDataFrame
    """

    # TODO: support a WKT geometry field too, e.g.
    # from shapely import wkt
    # df['Coordinates'] = df['Coordinates'].apply(wkt.loads)

    # TODO: validate lon,lat are in WGS84
    LOGGER.info("Reading: %s", csv_file)

    csv_df = pd.read_csv(csv_file)
    assert isinstance(csv_df[lon_field], pd.Series)
    assert isinstance(csv_df[lat_field], pd.Series)

    LOGGER.info("Composing GeoDataFrame with EPSG:4326")
    csv_gdf = gpd.GeoDataFrame(
        csv_df,
        geometry=gpd.points_from_xy(csv_df[lon_field], csv_df[lat_field]),
        crs="EPSG:4326",
    )

    # Note: don't do a merge of two GeoDataFrames like this, it can result in extra rows
    # uuid_gdf = gpd.GeoDataFrame({"geometry": csv_gdf.geometry, "uuid": uuids})
    # csv_gdf.merge(uuid_gdf)

    if add_uuid:
        gdf_with_uuid(csv_gdf)

    if add_s2:
        gdf_with_google_s2(csv_gdf)

    return csv_gdf


def geojson_from_csv_file(
    csv_file: Union[Path, str],
    lon_field: str = "longitude",
    lat_field: str = "latitude",
) -> Dict:
    """
    Read a CSV file that contains WGS84 longitude and latitude
    columns for point geometries

    .. seealso::
        - https://geopandas.org/gallery/create_geopandas_from_pandas.html

    :param csv_file: a string or Path to a CSV file
    :param lon_field: the name of the longitude column
    :param lat_field: the name of the latitude column
    :return: a geojson feature collection (as dict)
    """
    csv_gdf = gdf_from_csv_file(csv_file, lon_field, lat_field)
    return geojson_from_gdf(csv_gdf)


def geojson_limit_features(
    collection: Dict, offset: int = None, limit: int = None
) -> Tuple[Dict, int]:
    """
    Limit GeoJSON features

    :param collection: a geojson feature collection
    :param offset: Optional start index for the features to return
    :param limit: Optional upper limit on the number of features to return
    :return: tuple of (geojson, total_features)
    """
    total_features = len(collection["features"])
    LOGGER.debug("Total collection['features']: %s", total_features)
    if offset is not None and limit is not None:
        offset = int(offset)
        limit = int(limit)
        LOGGER.debug("Limit features with offset: %s, limit: %s", offset, limit)
        collection["features"] = collection["features"][offset : offset + limit]
    return collection, total_features


def geojson_fields(geojson_feature: Dict, sort: bool = False) -> List[str]:
    """
    Extract property fields from a geojson Feature

    These fields can be used to convert GeoJSON data to CSV.  The fields
    can be sorted as an option; the default order is based on the
    ordered dictionary for the property keys (plus 'wkt').

    .. code-block::

        geojson_feature = geojson["features"][0]
        fields = geojson_fields(geojson_feature)

    Assuming the fields are consistent across all the geojson features, this
    list of fields can be used to extract all the values into lists with a
    consistent order of values.  A generic 'wkt' field is added to hold a
    Well Known Text (wtk) representation of feature geometry.

    :param geojson_feature: a geojson Feature
    :param sort: sort the fields (defaults to False)
        In recent versions of python, the `properties` dictionary will be
        an ordered dictionary, so the order of the fields in the returned
        list should be consistent and based on the order of the property keys.
    :return: a list of property fields, which are all assumed
        to be the field names of the feature-properties in the geojson;
        it will be constructed from the geojson feature-properties.
    """
    csv_fields = list(geojson_feature["properties"].keys())
    if sort:
        csv_fields = sorted(csv_fields)
    return csv_fields + ["wkt"]


def geojson_to_csv(geojson_data: Dict, csv_fields: List[str] = None) -> List[List]:
    """
    Convert geojson FeatureCollection to CSV lists

    This can be used to convert geojson to CSV and save a CSV file, e.g. assuming
    the geojson_data contains features with a Point geometry:

    .. code-block::

        import csv
        import json

        with open("input.geojson", "r") as geojson_fd:
            geojson_data = json.load(geojson_fd)

        feature = geojson_data["features"][0]
        fields = geojson_fields(feature)
        csv_rows = geojson_to_csv(geojson_data, csv_fields=fields)

        with open('csv_file.csv', "w") as f:
            csv_writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerows(csv_rows)

    :param geojson_data: a geojson FeatureCollection
    :param csv_fields: an optional list of CSV header fields, which are all assumed
        to be the field names of the feature-properties in the geojson_data;
        if this is not provided, it will be constructed from the properties
        of the first feature in the geojson_data["features"] (with the
        assumption that feature coordinates can be represented as WKT).
    :return: a list of one or more lists with CSV values in each list; the
        first list is the fields of the CSV header
    """
    if csv_fields is None:
        feature = geojson_data["features"][0]
        csv_fields = geojson_fields(feature)

    csv_rows = [csv_fields]
    for feature in geojson_data["features"]:
        properties = feature["properties"]
        csv_row = []
        for field in csv_fields:
            if field in ["wkt", "WKT"]:
                wkt = shapely.geometry.shape(feature["geometry"]).wkt
                csv_row.append(wkt)
            else:
                csv_row.append(properties.get(field))
        csv_rows.append(csv_row)

    return csv_rows


def geojson_file_to_csv_file(
    geojson_file: str, csv_file: str = None, csv_fields: List[str] = None
) -> str:
    """
    Convert geojson file to csv file

    :param geojson_file: a file path string for a .geojson file
        that is assumed to contain a geojson FeatureCollection
    :param csv_file: an optional file path string for a .csv file; if it is
        not provided, the geojson_file is used to output a new .csv file with
        the same file path and file name.
    :param csv_fields: an optional list of CSV header fields, which are all assumed
        to be the field names of the feature-properties in the geojson file;
        if this is not provided, it will be constructed from the geojson
        feature-properties (with the assumption that the coordinates can
        be represented as WKT values).
    :return: CSV file (a file path string)
    """
    if csv_file is None:
        csv_file = str(Path(geojson_file).with_suffix(".csv"))

    LOGGER.debug("Converting from geojson: %s", geojson_file)
    LOGGER.debug("Converting to csv: %s", csv_file)

    with open(geojson_file, "r") as geojson_fd:
        geojson_data = geojson.load(geojson_fd)

    csv_rows = geojson_to_csv(geojson_data, csv_fields)

    with open(csv_file, "w") as f:
        csv_writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        csv_writer.writerows(csv_rows)

    return csv_file


def geojsons_dump(geojson_features: List[Dict], geojsons_file: str) -> Optional[str]:
    """
    :param geojson_features: a list of geojson features; from any
        feature collection, this is geojson_collection["features"]
    :param geojsons_file: a file path to write
    :return: if the dump succeeds, return the geojsons_file, or None
    """
    LOGGER.info("Saving GeoJSONSeq to %s", geojsons_file)
    with open(geojsons_file, "w") as dst:
        for feature in geojson_features:
            geojson.dump(feature, dst)
            dst.write("\n")

    geojsons_path = Path(geojsons_file)
    if geojsons_path.is_file() and geojsons_path.stat().st_size > 0:
        return geojsons_file


def geojsons_load(geojsons_file: Union[Path, str]) -> List[Dict]:
    """
    Read GeoJSON Text Sequence data from a file

    :param geojsons_file: a file path to write
    :return: geojson features

    .. seealso::

        - https://tools.ietf.org/html/rfc8142

    """
    file = Path(geojsons_file)
    assert file.exists()
    file_content = file.read_text()
    geojsons = file_content.splitlines()
    # some geojsons lines could be empty
    features = []
    while geojsons:
        feature = geojsons.pop(0).strip()
        if feature:
            features.append(json.loads(feature))
    return features


def geojsons_yield(geojsons_file: Union[Path, str]) -> Generator[Dict, None, None]:
    """
    Read GeoJSON Text Sequence data from a file
    and yield each geojson feature for each line

    :param geojsons_file: a file path to write
    :return: yield geojson features

    .. seealso::

        - https://tools.ietf.org/html/rfc8142

    """
    file = Path(geojsons_file)
    assert file.exists()
    with open(file, "r") as fd:
        while True:
            feature_line = fd.readline()
            if not feature_line:
                break
            # some geojsons lines could be empty
            feature = feature_line.strip()
            if feature:
                yield json.loads(feature)


def verify_geojson_output(file: Path) -> bool:
    if not file.suffix == ".geojson":
        return False
    if file.exists() and file.stat().st_size > 0:
        with open(file, "r") as fd:
            geojson.load(fd)
            return True
    return False


def verify_json_output(file: Path) -> bool:
    if not file.suffix == ".json":
        return False
    if file.exists() and file.stat().st_size > 0:
        with open(file, "r") as fd:
            json.load(fd)
            return True
    return False
