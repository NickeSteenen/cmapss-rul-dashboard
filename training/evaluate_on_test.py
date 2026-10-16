import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn import metrics
from sklearn.dummy import DummyRegressor

from project_settings import (
    COMBINED_TEST_DATA_PATH,
    COMPLETE_TRAINING_DATA_PATH,
    DATASETS,
    MODEL_PATH,
    PREDICTED_VS_TRUE_RUL_PLOT_PATH,
    RESULTS_DIR,
    TEST_SCORES_PATH,
    TRUE_RUL_PER_TEST_DATA_CYCLE_PATH,
)


def get_last_cycle_per_engine(df):
    last_cycle_idx = df.groupby(["source_dataset", "unit"])["cycle"].idxmax()
    return df.loc[last_cycle_idx].reset_index(drop=True)


def mae_and_rmse(true_rul, predicted_rul):
    return metrics.mean_absolute_error(true_rul, predicted_rul), metrics.root_mean_squared_error(true_rul, predicted_rul)


def score_table(engines):
    lines = [
        "| Dataset | Test engines | Model MAE | Model RMSE | Baseline MAE | Baseline RMSE |",
        "|---|---|---|---|---|---|",
    ]
    groups = [(name, engines[engines["source_dataset"] == name]) for name in DATASETS] + [("All", engines)]
    for name, group in groups:
        model_mae, model_rmse = mae_and_rmse(group["RUL"], group["model_prediction"])
        baseline_mae, baseline_rmse = mae_and_rmse(group["RUL"], group["baseline_prediction"])
        lines.append(f"| {name} | {len(group)} | {model_mae:.2f} | {model_rmse:.2f} | {baseline_mae:.2f} | {baseline_rmse:.2f} |")
    return "\n".join(lines)


TRUE_RUL_RANGES = [(0, 25, "under 25"), (25, 50, "25-50"), (50, 100, "50-100"), (100, 150, "100-150"),
                   (150, 200, "150-200"), (200, float("inf"), "200 and above")]


def error_by_distance_to_failure_table(rows):
    lines = [
        "| True RUL (cycles) | Cycles | Model MAE | Average predicted − true |",
        "|---|---|---|---|",
    ]
    for lowest, below, name in TRUE_RUL_RANGES:
        group = rows[(rows["RUL"] >= lowest) & (rows["RUL"] < below)]
        error = group["model_prediction"] - group["RUL"]
        lines.append(f"| {name} | {len(group)} | {error.abs().mean():.2f} | {error.mean():+.2f} |")
    return "\n".join(lines)


def plot_predicted_vs_true_rul(engines, path):
    fig, ax = plt.subplots(figsize=(7, 7))
    for name in DATASETS:
        group = engines[engines["source_dataset"] == name]
        ax.scatter(group["RUL"], group["model_prediction"], s=12, label=name)
    top = max(engines["RUL"].max(), engines["model_prediction"].max())
    ax.plot([0, top], [0, top], color="black", linewidth=1, label="Perfect prediction")
    ax.set_xlabel("True RUL (cycles)")
    ax.set_ylabel("Predicted RUL (cycles)")
    ax.set_title("Predicted vs true RUL at each test engine's last row")
    ax.legend()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    test_df = pd.read_csv(COMBINED_TEST_DATA_PATH)
    last_cycle_df = get_last_cycle_per_engine(test_df)  # scored on each engine's last row, like the RUL_FDxxx files
    test_rul_df = pd.read_csv(TRUE_RUL_PER_TEST_DATA_CYCLE_PATH)
    last_rows_with_true_rul = last_cycle_df.merge(test_rul_df, on=["source_dataset", "unit", "cycle"])
    if len(last_rows_with_true_rul) != len(last_cycle_df):
        raise ValueError(f"{len(last_cycle_df)} test engines, but only {len(last_rows_with_true_rul)} have a true RUL for their last row")
    model = joblib.load(MODEL_PATH)
    feature_columns = list(model.feature_names_in_)
    last_rows_with_true_rul["model_prediction"] = model.predict(last_rows_with_true_rul[feature_columns])

    # Always guesses the average RUL of the training rows. It gets all training rows, while the model was trained on
    # 80% of the training engines, so if anything the comparison favours the baseline.
    train_df = pd.read_csv(COMPLETE_TRAINING_DATA_PATH)
    baseline = DummyRegressor(strategy="mean").fit(train_df[feature_columns], train_df["RUL"])
    last_rows_with_true_rul["baseline_prediction"] = baseline.predict(last_rows_with_true_rul[feature_columns])

    table = score_table(last_rows_with_true_rul)
    print(table)

    # Every cycle of every test engine, not just the last, to see how the error changes with the distance to failure
    all_rows_with_true_rul = test_df.merge(test_rul_df, on=["source_dataset", "unit", "cycle"])
    all_rows_with_true_rul["model_prediction"] = model.predict(all_rows_with_true_rul[feature_columns])
    distance_table = error_by_distance_to_failure_table(all_rows_with_true_rul)
    print()
    print(distance_table)

    RESULTS_DIR.mkdir(exist_ok=True)
    TEST_SCORES_PATH.write_text(
        f"Scored on each test engine's last row ({len(last_rows_with_true_rul)} engines). "
        f"The baseline always guesses the average RUL of the training rows ({baseline.constant_[0][0]:.1f} cycles).\n\n"
        f"{table}\n\n"
        f"Error by distance to failure, over every cycle of every test engine ({len(all_rows_with_true_rul)} cycles), "
        f"grouped by the true RUL. A positive average means the model predicted more remaining life than there was.\n\n"
        f"{distance_table}\n",
        encoding="utf-8",
    )
    plot_predicted_vs_true_rul(last_rows_with_true_rul, PREDICTED_VS_TRUE_RUL_PLOT_PATH)
    print(f"Saved {TEST_SCORES_PATH} and {PREDICTED_VS_TRUE_RUL_PLOT_PATH}")
