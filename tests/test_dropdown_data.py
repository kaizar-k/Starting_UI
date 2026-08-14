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
