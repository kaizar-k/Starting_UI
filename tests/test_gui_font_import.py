import subprocess
import sys


def test_gui_imports_without_root_window():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import gui.controls.label",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )

    assert result.returncode == 0, result.stderr
