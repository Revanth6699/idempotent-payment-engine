from __future__ import annotations

import numpy as np
import pandas as pd


class SyntheticTransactionDatasetService:
    """Generates synthetic transaction data for anomaly-model experiments."""

    DEFAULT_SAMPLE_COUNT = 1000
    DEFAULT_ANOMALY_RATE = 0.05
    RANDOM_STATE = 42

    @classmethod
    def generate(
        cls,
        sample_count: int = DEFAULT_SAMPLE_COUNT,
        anomaly_rate: float = DEFAULT_ANOMALY_RATE,
        random_state: int = RANDOM_STATE,
    ) -> pd.DataFrame:
        """Generate a reproducible synthetic transaction dataset."""

        if sample_count < 10:
            raise ValueError("sample_count must be at least 10")

        if not 0.0 < anomaly_rate < 1.0:
            raise ValueError("anomaly_rate must be between 0 and 1")

        rng = np.random.default_rng(random_state)

        anomaly_count = max(
            1,
            int(round(sample_count * anomaly_rate)),
        )

        anomaly_indexes = rng.choice(
            sample_count,
            size=anomaly_count,
            replace=False,
        )

        is_anomaly = np.zeros(
            sample_count,
            dtype=bool,
        )
        is_anomaly[anomaly_indexes] = True

        transaction_amount = rng.lognormal(
            mean=6.0,
            sigma=0.7,
            size=sample_count,
        )

        transactions_last_24h = rng.poisson(
            lam=4.0,
            size=sample_count,
        )

        average_amount_30d = rng.lognormal(
            mean=5.8,
            sigma=0.5,
            size=sample_count,
        )

        amount_deviation_ratio = (
            transaction_amount
            / np.maximum(average_amount_30d, 1.0)
        )

        failed_attempts_24h = rng.poisson(
            lam=0.5,
            size=sample_count,
        )

        transaction_hour = rng.integers(
            low=0,
            high=24,
            size=sample_count,
        )

        account_age_days = rng.integers(
            low=30,
            high=2500,
            size=sample_count,
        )

        international_transaction = rng.binomial(
            n=1,
            p=0.15,
            size=sample_count,
        )

        # Inject deliberately unusual transaction behaviour.
        transaction_amount[is_anomaly] *= rng.uniform(
            8.0,
            20.0,
            size=anomaly_count,
        )

        transactions_last_24h[is_anomaly] += rng.integers(
            15,
            40,
            size=anomaly_count,
        )

        amount_deviation_ratio[is_anomaly] *= rng.uniform(
            6.0,
            15.0,
            size=anomaly_count,
        )

        failed_attempts_24h[is_anomaly] += rng.integers(
            5,
            12,
            size=anomaly_count,
        )

        transaction_hour[is_anomaly] = rng.choice(
            [0, 1, 2, 3, 4],
            size=anomaly_count,
        )

        account_age_days[is_anomaly] = rng.integers(
            1,
            30,
            size=anomaly_count,
        )

        international_transaction[is_anomaly] = 1

        return pd.DataFrame(
            {
                "transaction_id": [
                    f"SYN-TXN-{index + 1:06d}"
                    for index in range(sample_count)
                ],
                "transaction_amount": transaction_amount,
                "transactions_last_24h": transactions_last_24h,
                "average_amount_30d": average_amount_30d,
                "amount_deviation_ratio": amount_deviation_ratio,
                "failed_attempts_24h": failed_attempts_24h,
                "transaction_hour": transaction_hour,
                "account_age_days": account_age_days,
                "international_transaction": international_transaction,
                "ground_truth_anomaly": is_anomaly,
            }
        )