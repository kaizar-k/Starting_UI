import pandas as pd

from backend.dropdown_backend import DropdownData


def test_get_configuration_values_by_name_returns_matching_row(tmp_path):
    configurations_path = tmp_path / "configurations.csv"
    pd.DataFrame(
        [
            {
                "configuration_name": "example1",
                "AC/DC": "AC",
                "Sensor Type": "loop",
                "Substrate": "substrate 1",
                "Graphene": "graphene 1",
                "Coating": "coating 1",
                "calibration_regimes": "regime 1",
            },
            {
                "configuration_name": "example2",
                "AC/DC": "DC",
                "Sensor Type": "loop",
                "Substrate": "substrate 2",
                "Graphene": "graphene 2",
                "Coating": "coating 2",
                "calibration_regimes": "regime 2",
            },
        ]
    ).to_csv(configurations_path, index=False)

    dropdown_data = DropdownData(configurations_csv_path=str(configurations_path))

    assert dropdown_data.get_configuration_values_by_name("example1") == {
        "configuration_name": "example1",
        "AC/DC": "AC",
        "Sensor Type": "loop",
        "Substrate": "substrate 1",
        "Graphene": "graphene 1",
        "Coating": "coating 1",
        "calibration_regimes": "regime 1",
    }

    assert dropdown_data.find_configuration_name_for_values({
        "AC/DC": "AC",
        "Sensor Type": "loop",
        "Substrate": "substrate 1",
        "Graphene": "graphene 1",
        "Coating": "coating 1",
    }) == "example1"

    assert dropdown_data.find_configuration_name_for_values({
        "AC/DC": "AC",
        "Sensor Type": "loop",
        "Substrate": "substrate 9",
        "Graphene": "graphene 1",
        "Coating": "coating 1",
    }) is None
