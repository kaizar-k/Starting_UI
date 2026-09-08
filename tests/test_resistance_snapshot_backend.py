"""Regression tests for listing and removing saved trial snapshots."""

import pandas as pd

from backend.resistance_snapshot_backend import TrialSnapshotBackend


def test_get_all_trial_ids_returns_empty_list_when_csv_missing(tmp_path):
    backend = TrialSnapshotBackend(str(tmp_path / "trial_data.csv"))

    assert backend.get_all_trial_ids() == []


def test_get_trial_display_options_include_shape_labels(tmp_path):
    csv_path = tmp_path / "trial_data.csv"
    backend = TrialSnapshotBackend(str(csv_path))
    backend.save_snapshot([1.0] * 12, "circle")
    backend.save_snapshot([2.0] * 12, "giffy")

    assert backend.get_trial_display_options() == [
        "Trial 1 (circle)",
        "Trial 2 (giffy)",
    ]


def test_remove_trial_deletes_only_matching_row(tmp_path):
    csv_path = tmp_path / "trial_data.csv"
    backend = TrialSnapshotBackend(str(csv_path))
    backend.save_snapshot([1.0] * 12, "circle")
    backend.save_snapshot([2.0] * 12, "square")
    backend.save_snapshot([3.0] * 12, "triangle")

    assert backend.remove_trial(2) is True

    df = pd.read_csv(csv_path)
    assert list(df["trial_ID"]) == [1, 3]
    assert list(df["shape"]) == ["circle", "triangle"]


def test_remove_trial_returns_false_for_missing_trial_id(tmp_path):
    csv_path = tmp_path / "trial_data.csv"
    backend = TrialSnapshotBackend(str(csv_path))
    backend.save_snapshot([1.0] * 12, "circle")

    assert backend.remove_trial(999) is False

    df = pd.read_csv(csv_path)
    assert list(df["trial_ID"]) == [1]


def test_save_after_removal_uses_next_available_id(tmp_path):
    csv_path = tmp_path / "trial_data.csv"
    backend = TrialSnapshotBackend(str(csv_path))
    backend.save_snapshot([1.0] * 12, "circle")
    backend.save_snapshot([2.0] * 12, "square")
    backend.save_snapshot([3.0] * 12, "triangle")

    assert backend.remove_trial(2) is True
    next_trial_id = backend.save_snapshot([4.0] * 12, "rectangle")

    assert next_trial_id == 4
    df = pd.read_csv(csv_path)
    assert list(df["trial_ID"]) == [1, 3, 4]
