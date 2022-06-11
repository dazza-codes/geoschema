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

from copy import deepcopy
from types import GeneratorType
from typing import Dict

import pytest

from geoschema.geojson_utils import geojsons_load
from geoschema.geojson_utils import geojsons_yield


@pytest.fixture
def station_feature() -> Dict:
    return deepcopy(
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-118.365379, 34.199669]},
            "properties": {
                "stid": "KBUR",
                "elevation": 728,
                "mnet_id": 1,
                "name": "Burbank - Bob Hope Airport",
                "acquired_at": "2020-05-11T20:55:00",
                "air_temp": 23,
                "relative_humidity": 46.78,
                "wind_gust": 9.26,
                "wind_speed": 3.6,
                "wind_direction": 200,
            },
        }
    )


def test_geojsons_yield(geojsons_stations_file, station_feature):
    geojsons = geojsons_yield(geojsons_stations_file)
    assert isinstance(geojsons, GeneratorType)
    features = list(geojsons)
    assert len(features) == 2
    assert features[0] == station_feature


def test_geojsons_load(geojsons_stations_file, station_feature):
    features = geojsons_load(geojsons_stations_file)
    assert len(features) == 2
    assert features[0] == station_feature
