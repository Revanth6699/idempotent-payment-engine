import pandas as pd
import pytest

from backend.app.ml.synthetic_transaction_dataset_service import (
    SyntheticTransactionDatasetService,
)


def test_generate_returns_requested_sample_count():
    dataset = SyntheticTransactionDatasetService.generate(
        sample_count=200,
    )

    assert isinstance(dataset, pd.DataFrame)
    assert len(dataset) == 200


def test_generate_contains_required_columns():
    dataset = SyntheticTransactionDatasetService.generate(
        sample_count=200,
    )

    expected_columns = {
        "transaction_id",
        "transaction_amount",
        "transactions_last_24h",
        "average_amount_30d",
        "amount_deviation_ratio",
        "failed_attempts_24h",
        "transaction_hour",
        "account_age_days",
        "international_transaction",
        "ground_truth_anomaly",
    }

    assert expected_columns.issubset(dataset.columns)


def test_generate_produces_positive_transaction_amounts():
    dataset = SyntheticTransactionDatasetService.generate(
        sample_count=200,
    )

    assert (dataset["transaction_amount"] > 0).all()
    assert (dataset["average_amount_30d"] > 0).all()


def test_generate_injects_expected_anomaly_rate():
    dataset = SyntheticTransactionDatasetService.generate(
        sample_count=1000,
        anomaly_rate=0.05,
    )

    anomaly_count = int(
        dataset["ground_truth_anomaly"].sum()
    )

    assert anomaly_count == 50


def test_generate_is_reproducible():
    first = SyntheticTransactionDatasetService.generate(
        sample_count=200,
        random_state=42,
    )

    second = SyntheticTransactionDatasetService.generate(
        sample_count=200,
        random_state=42,
    )

    pd.testing.assert_frame_equal(first, second)


def test_generate_changes_with_different_random_state():
    first = SyntheticTransactionDatasetService.generate(
        sample_count=200,
        random_state=42,
    )

    second = SyntheticTransactionDatasetService.generate(
        sample_count=200,
        random_state=99,
    )

    assert not first.equals(second)


def test_generate_rejects_invalid_sample_count():
    with pytest.raises(ValueError):
        SyntheticTransactionDatasetService.generate(
            sample_count=5,
        )


def test_generate_rejects_invalid_anomaly_rate():
    with pytest.raises(ValueError):
        SyntheticTransactionDatasetService.generate(
            sample_count=100,
            anomaly_rate=0.0,
        )

    with pytest.raises(ValueError):
        SyntheticTransactionDatasetService.generate(
            sample_count=100,
            anomaly_rate=1.0,
        )