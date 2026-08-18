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
