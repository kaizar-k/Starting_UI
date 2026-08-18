import pandas as pd

from backend.dropdown_backend import DropdownData


def test_get_used_options_by_category_reads_configurations_csv(tmp_path):
    options_path = tmp_path / "options.csv"
    configurations_path = tmp_path / "configurations.csv"

    pd.DataFrame(
        [
            {"configuration_name": "example1", "AC/DC": "AC", "Sensor Type": "loop", "Substrate": "substrate 1"},
            {"configuration_name": "example2", "AC/DC": "DC", "Sensor Type": "loop", "Substrate": "substrate 2"},
        ]
    ).to_csv(configurations_path, index=False)

    dropdown_data = DropdownData(
        options_csv_path=str(options_path),
        configurations_csv_path=str(configurations_path),
    )

    assert dropdown_data.get_used_options_by_category() == {
        "AC/DC": ["AC", "DC"],
        "Sensor Type": ["loop"],
        "Substrate": ["substrate 1", "substrate 2"],
    }


def test_dropdown_options_are_naturally_sorted(tmp_path):
    options_path = tmp_path / "options.csv"
    configurations_path = tmp_path / "configurations.csv"

    pd.DataFrame(
        [
            {"category": "Sensor Type", "value": "10 Loops"},
            {"category": "Sensor Type", "value": "2 Loops"},
            {"category": "Sensor Type", "value": "1 Loop"},
        ]
    ).to_csv(options_path, index=False)
    pd.DataFrame(
        [
            {"configuration_name": "10 Loops Setup", "Sensor Type": "10 Loops"},
            {"configuration_name": "2 Loops Setup", "Sensor Type": "2 Loops"},
            {"configuration_name": "1 Loop Setup", "Sensor Type": "1 Loop"},
        ]
    ).to_csv(configurations_path, index=False)

    dropdown_data = DropdownData(
        options_csv_path=str(options_path),
        configurations_csv_path=str(configurations_path),
    )

    assert dropdown_data.get_options_by_category()["Sensor Type"] == ["1 Loop", "2 Loops", "10 Loops"]
    assert dropdown_data.get_used_options_by_category()["Sensor Type"] == ["1 Loop", "2 Loops", "10 Loops"]


def test_dropdown_options_sort_without_case_sensitivity(tmp_path):
    options_path = tmp_path / "options.csv"
    pd.DataFrame(
        [
            {"category": "Sensor Type", "value": "S6"},
            {"category": "Sensor Type", "value": "example11"},
            {"category": "Sensor Type", "value": "example1"},
        ]
    ).to_csv(options_path, index=False)

    dropdown_data = DropdownData(options_csv_path=str(options_path))

    assert dropdown_data.get_options_by_category()["Sensor Type"] == ["example1", "example11", "S6"]
