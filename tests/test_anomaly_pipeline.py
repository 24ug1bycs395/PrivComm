import pandas as pd

from ml.anomaly.generate_dataset import generate_controlled_dataset
from ml.anomaly.schemas import FEATURE_COLUMNS, validate_dataframe


def test_controlled_generator_is_reproducible_and_schema_valid():
    first = generate_controlled_dataset("traffic_spike", 8, seed=7)
    second = generate_controlled_dataset("traffic_spike", 8, seed=7)
    pd.testing.assert_frame_equal(first, second)
    validated = validate_dataframe(first)
    assert validated[FEATURE_COLUMNS].shape == (8, len(FEATURE_COLUMNS))
    assert set(validated["label"]) == {1}


def test_normal_and_anomaly_scenarios_have_measurable_separation():
    normal = generate_controlled_dataset("normal", 100, seed=1)
    spike = generate_controlled_dataset("traffic_spike", 100, seed=1)
    assert spike["bytes_per_second"].median() > normal["bytes_per_second"].median()
    assert spike["packets_per_second"].median() > normal["packets_per_second"].median()
