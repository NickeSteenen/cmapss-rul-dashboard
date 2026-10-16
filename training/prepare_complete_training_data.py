import pandas as pd

from project_settings import COLUMN_NAMES, COMPLETE_TRAINING_DATA_PATH, DATA_DIR, DATASETS


def load_training_dataset(name):
    path = DATA_DIR / f"train_{name}.txt"
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMN_NAMES)
    df["source_dataset"] = name

    max_cycle_per_unit = df.groupby("unit")["cycle"].transform("max")
    df["RUL"] = max_cycle_per_unit - df["cycle"]

    return df


def build_complete_training_data():
    all_datasets = [load_training_dataset(name) for name in DATASETS]
    return pd.concat(all_datasets, ignore_index=True)


if __name__ == "__main__":
    complete_training_data = build_complete_training_data()
    complete_training_data.to_csv(COMPLETE_TRAINING_DATA_PATH, index=False)
    print(f"Saved {len(complete_training_data)} rows to {COMPLETE_TRAINING_DATA_PATH}")
