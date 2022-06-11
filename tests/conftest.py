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
Common test fixtures

pytest --fixtures
"""

import json
from pathlib import Path
from typing import Dict
from typing import List

import pytest


@pytest.fixture
def test_data_path() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def geojson_stations_file(test_data_path) -> str:
    """Sample GeoJSON feature collection with surface observations"""
    path = test_data_path / "stations.geojson"
    return str(path.absolute())


@pytest.fixture
def geojsons_stations_file(test_data_path) -> str:
    """Sample GeoJSONSeq features with surface observations"""
    path = test_data_path / "stations.geojsons"
    return str(path.absolute())


@pytest.fixture
def geojson_stations_data(geojson_stations_file) -> Dict:
    with open(geojson_stations_file) as json_fd:
        yield json.load(json_fd)


@pytest.fixture
def geojson_feature_collection(geojson_stations_data) -> Dict:
    return geojson_stations_data


@pytest.fixture
def geojson_features(geojson_stations_data) -> List[Dict]:
    return geojson_stations_data["features"]
