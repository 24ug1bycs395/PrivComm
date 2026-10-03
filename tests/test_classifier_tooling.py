import sys
from pathlib import Path

import numpy as np
import pytest

CLASSIFIER_SRC = Path(__file__).resolve().parents[1] / "traffic-classifier" / "src"
sys.path.insert(0, str(CLASSIFIER_SRC))

from evaluate import top_label_calibration
from preprocess import grouped_capture_split, preprocess_pipeline


def test_grouped_capture_split_is_reproducible_and_disjoint() -> None:
    groups = np.repeat([f"capture-{index}" for index in range(20)], 3)
    labels = np.tile([0, 1, 2], 20)
    features = np.arange(len(labels) * 2).reshape(len(labels), 2)

    train, validation, test = grouped_capture_split(features, labels, groups)
    repeated = grouped_capture_split(features, labels, groups)

    assert np.array_equal(train, repeated[0])
    assert np.array_equal(validation, repeated[1])
    assert np.array_equal(test, repeated[2])
    assert not set(groups[train]) & set(groups[validation])
    assert not set(groups[train]) & set(groups[test])
    assert not set(groups[validation]) & set(groups[test])


def test_top_label_calibration_reports_ece_and_multiclass_brier() -> None:
    result = top_label_calibration(
        np.array([0, 1, 0]),
        np.array([[0.9, 0.1], [0.6, 0.4], [0.2, 0.8]]),
        bins=2,
    )

    assert result["expected_calibration_error"] == pytest.approx(0.4333333333)
    assert result["multiclass_brier_score"] == pytest.approx(0.6733333333)
    assert sum(item["samples"] for item in result["bins"]) == 3


def test_preprocessing_keeps_capture_ids_for_split_but_not_features(tmp_path) -> None:
    import pandas as pd

    rows = []
    for capture_index in range(30):
        for label_index, label in enumerate(("ike", "esp", "other")):
            rows.append({
                "capture_id": f"capture-{capture_index}",
                "flow_id": f"flow-{capture_index}-{label_index}",
                "flowBytesPerSecond": capture_index + label_index + 1,
                "flowPktsPerSecond": capture_index + 2,
                "mean_fiat": capture_index + 3,
                "mean_biat": label_index + 1,
                "duration": capture_index + label_index + 2,
                "traffic_type": label,
            })
    dataset_path = tmp_path / "captures.csv"
    pd.DataFrame(rows).to_csv(dataset_path, index=False)

    schema = preprocess_pipeline(
        str(dataset_path),
        output_dir=str(tmp_path / "processed"),
        models_dir=str(tmp_path / "models"),
        remove_duplicates=False,
    )

    assert schema["group_column"] == "capture_id"
    assert "capture_id" not in schema["feature_columns"]
    assert "flow_id" not in schema["feature_columns"]
    assert schema["source_group_count"] == 30
    assert sum(schema["group_counts"].values()) == 30
    assert len(schema["group_hashes_by_split"]["train"]) == schema["group_counts"]["train"]
    assert not (
        set(schema["group_hashes_by_split"]["train"])
        & set(schema["group_hashes_by_split"]["validation"])
    )
    assert not (
        set(schema["group_hashes_by_split"]["train"])
        & set(schema["group_hashes_by_split"]["test"])
    )
    assert not (
        set(schema["group_hashes_by_split"]["validation"])
        & set(schema["group_hashes_by_split"]["test"])
    )
