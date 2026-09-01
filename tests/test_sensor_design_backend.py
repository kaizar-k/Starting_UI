import pytest

from backend.sensor_design_backend import SensorDesignBackend


@pytest.fixture
def backend():
    return SensorDesignBackend()


def test_ring_geometry_computes_area_from_radii(backend):
    points = [{
        "x": 10,
        "y": 20,
        "radius_outer": 3,
        "radius_inner": 1,
        "area": "",
    }]

    validated = backend.validate_sensing_points(points, [50, 50])

    assert validated[0]["area"] == pytest.approx(25.132741228718345)
    assert validated[0]["radius_outer"] == 3
    assert validated[0]["radius_inner"] == 1


def test_area_only_mode_allows_blank_radii(backend):
    points = [{
        "x": 10,
        "y": 20,
        "radius_outer": "",
        "radius_inner": "",
        "area": 12.5,
    }]

    validated = backend.validate_sensing_points(points, [50, 50])

    assert validated[0]["area"] == 12.5
    assert validated[0]["radius_outer"] == 0.0
    assert validated[0]["radius_inner"] == 0.0


def test_mixed_area_and_radii_is_rejected(backend):
    points = [{
        "x": 10,
        "y": 20,
        "radius_outer": 3,
        "radius_inner": 1,
        "area": 12.5,
    }]

    with pytest.raises(ValueError, match="sensor area not needed if inner and outer radii provided"):
        backend.validate_sensing_points(points, [50, 50])


def test_add_sensor_design_accepts_area_computed_by_form(tmp_path):
    backend = SensorDesignBackend(str(tmp_path / "design_data.csv"))
    points = backend.build_sensing_point_payload([{
        "x": 10,
        "y": 20,
        "radius_outer": "3",
        "radius_inner": "1",
        "area": "",
    }])

    backend.add_sensor_design("ring design", [50, 50], points)

    assert backend.get_sensor_type_options() == ["ring design"]


def test_sensor_design_options_are_naturally_sorted(tmp_path):
    design_data_path = tmp_path / "design_data.csv"
    design_data_path.write_text(
        "Sensor Design,Dimensions,Sensing Points\n"
        "10 Loops,\"[50, 50]\",\"[]\"\n"
        "2 Loops,\"[50, 50]\",\"[]\"\n"
        "1 Loop,\"[50, 50]\",\"[]\"\n",
        encoding="utf-8",
    )

    backend = SensorDesignBackend(str(design_data_path))

    assert backend.get_sensor_type_options() == ["1 Loop", "2 Loops", "10 Loops"]


def _add_design_with_point_count(backend, name, point_count):
    points = [
        backend.build_sensing_point_payload([{
            "x": 5, "y": 5, "radius_outer": "1", "radius_inner": "0", "area": "",
        }])[0]
        for _ in range(point_count)
    ]
    backend.add_sensor_design(name, [50, 50], points)


def test_build_channel_map_matches_worked_example(tmp_path):
    # Channel 1 is reserved, so four points run across channels 2-5.
    backend = SensorDesignBackend(str(tmp_path / "design_data.csv"))
    _add_design_with_point_count(backend, "3-point design", 3)
    _add_design_with_point_count(backend, "1-point design", 1)
    backend.set_layer_sensor_type(1, "3-point design")
    backend.set_layer_sensor_type(2, "1-point design")

    channel_map = backend.build_channel_map(2)

    assert channel_map == {1: [2, 3, 4], 2: [5]}
    assert backend.get_total_channel_count(2) == 4
    assert backend.get_required_device_channel_count(2) == 5


def test_build_channel_map_skips_unconfigured_layers_without_gaps(tmp_path):
    # Layer 2 has no sensor design selected, so it contributes zero channels
    # and layer 3's channels immediately follow layer 1's after channel 1.
    backend = SensorDesignBackend(str(tmp_path / "design_data.csv"))
    _add_design_with_point_count(backend, "2-point design", 2)
    backend.set_layer_sensor_type(1, "2-point design")
    backend.set_layer_sensor_type(3, "2-point design")

    channel_map = backend.build_channel_map(3)

    assert channel_map == {1: [2, 3], 2: [], 3: [4, 5]}
    assert backend.get_total_channel_count(3) == 4
    assert backend.get_required_device_channel_count(3) == 5


def test_build_channel_map_all_layers_unconfigured(tmp_path):
    backend = SensorDesignBackend(str(tmp_path / "design_data.csv"))

    channel_map = backend.build_channel_map(2)

    assert channel_map == {1: [], 2: []}
    assert backend.get_total_channel_count(2) == 0
    assert backend.get_required_device_channel_count(2) == 0
