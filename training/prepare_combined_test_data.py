import pandas as pd

from project_settings import COLUMN_NAMES, COMBINED_TEST_DATA_PATH, DATA_DIR, DATASETS, TRUE_RUL_PER_TEST_DATA_CYCLE_PATH


def load_test_dataset(name):
    path = DATA_DIR / f"test_{name}.txt"
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMN_NAMES)
    df["source_dataset"] = name  # unit numbers restart at 1 in every dataset, so they need this to stay unique
    return df


def build_combined_test_data():
    all_datasets = [load_test_dataset(name) for name in DATASETS]
    return pd.concat(all_datasets, ignore_index=True)


def load_rul_file(name):
    # One number per line, line N for engine N, giving the RUL after that engine's last test row
    path = DATA_DIR / f"RUL_{name}.txt"
    values = pd.read_csv(path, header=None, names=["rul_after_last_cycle"])["rul_after_last_cycle"]
    return pd.DataFrame({
        "source_dataset": name,
        "unit": range(1, len(values) + 1),
        "rul_after_last_cycle": values.values,
    })


def build_true_rul_per_test_data_cycle(test_data):
    rul_files = pd.concat([load_rul_file(name) for name in DATASETS], ignore_index=True)
    engines = test_data.groupby(["source_dataset", "unit"])["cycle"].max().rename("last_cycle").reset_index()

    per_engine = engines.merge(rul_files, on=["source_dataset", "unit"])
    if not (len(per_engine) == len(engines) == len(rul_files)):
        raise ValueError(f"{len(engines)} test engines and {len(rul_files)} RUL lines, but only {len(per_engine)} were paired")

    rows = test_data[["source_dataset", "unit", "cycle"]].merge(per_engine, on=["source_dataset", "unit"])
    rows["RUL"] = rows["rul_after_last_cycle"] + rows["last_cycle"] - rows["cycle"]  # each earlier cycle has one more flight left
    return rows[["source_dataset", "unit", "cycle", "RUL"]]


if __name__ == "__main__":
    combined_test_data = build_combined_test_data()
    combined_test_data.to_csv(COMBINED_TEST_DATA_PATH, index=False)
    print(f"Saved {len(combined_test_data)} rows to {COMBINED_TEST_DATA_PATH}")

    # The true RUL goes in its own file, so the senders can never stream it
    true_rul_per_test_data_cycle = build_true_rul_per_test_data_cycle(combined_test_data)
    true_rul_per_test_data_cycle.to_csv(TRUE_RUL_PER_TEST_DATA_CYCLE_PATH, index=False)
    print(f"Saved {len(true_rul_per_test_data_cycle)} rows to {TRUE_RUL_PER_TEST_DATA_CYCLE_PATH}")
