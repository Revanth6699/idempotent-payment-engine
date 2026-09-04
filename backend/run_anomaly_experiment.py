from backend.app.ml.anomaly_experiment_service import (
    AnomalyExperimentService,
)
from backend.app.ml.synthetic_transaction_dataset_service import (
    SyntheticTransactionDatasetService,
)


def main() -> None:
    dataset = SyntheticTransactionDatasetService.generate(
        sample_count=1000,
        anomaly_rate=0.05,
        random_state=42,
    )

    print("\n=== Running anomaly-model experiments ===\n")

    evaluations = AnomalyExperimentService.run_all_experiments(
        dataset
    )

    descriptive_results = (
        AnomalyExperimentService.evaluations_to_dataframe(
            evaluations
        )
    )

    print("=== Descriptive anomaly results ===")
    print(descriptive_results.to_string(index=False))

    print("\n=== Ground-truth evaluation ===")

    evaluation = AnomalyExperimentService.evaluate_all_models(
        dataset
    )

    print(evaluation.to_string(index=False))

    selected_model, selection_results = (
        AnomalyExperimentService.run_model_selection(
            dataset
        )
    )

    print("\n=== Final model selection ===")
    print(selection_results.to_string(index=False))
    print(f"\nSelected model: {selected_model}")


if __name__ == "__main__":
    main()