import math

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from project_settings import COMPLETE_TRAINING_DATA_PATH

SIGNALS = ["setting1", "setting2", "setting3"] + [f"sensor{i}" for i in range(1, 22)]
SPARE_ROOM = 0.10  # extra room added below the lowest and above the highest value, as a share of the range
STEP_CANDIDATES = [1, 0.1, 0.01, 0.001, 0.0001]  # coarsest first, since coarser steps need fewer bits
N_SPLITS = 20  # how many different splits to try when checking the spare room
FLOAT_TOLERANCE = 1e-9  # absorbs floating-point error, and is far smaller than the finest step (0.0001)


def engine_ids(df):
    return df["source_dataset"] + "_" + df["unit"].astype(str)  # unit numbers restart at 1 in every dataset


def largest_exact_step(name, values):
    for step in STEP_CANDIDATES:
        # rtol=0: the default relative tolerance would accept steps that are too coarse for large values
        if np.allclose(np.round(values / step) * step, values, rtol=0, atol=FLOAT_TOLERANCE):
            return step
    raise ValueError(f"{name} needs a step finer than {STEP_CANDIDATES[-1]}")


def bits_for(steps):
    return max(1, math.ceil(math.log2(steps + 1)))  # bits needed to count from 0 up to `steps`


def largest_overshoot_by_new_engines(train):
    """How far engines the design hasn't seen go outside the range of the ones it has, as a share of that range."""
    splitter = GroupShuffleSplit(n_splits=N_SPLITS, test_size=0.2, random_state=42)
    worst, worst_signal = 0.0, None
    for a_idx, b_idx in splitter.split(train, groups=engine_ids(train)):
        group_a, group_b = train.iloc[a_idx], train.iloc[b_idx]  # A = engines we "know", B = engines we pretend are new
        for name in SIGNALS:
            lowest, highest = group_a[name].min(), group_a[name].max()
            below = lowest - group_b[name].min()
            above = group_b[name].max() - highest
            outside = max(0, below, above) / (highest - lowest)
            if outside > worst:
                worst, worst_signal = outside, name
    return worst, worst_signal


def design_signal(name, values):
    step = largest_exact_step(name, values)
    lowest, highest = values.min(), values.max()
    spare = SPARE_ROOM * (highest - lowest)

    start = math.floor((lowest - spare) / step + FLOAT_TOLERANCE) * step
    steps_needed = math.ceil((highest + spare - start) / step - FLOAT_TOLERANCE)
    bits = bits_for(steps_needed)
    top = start + (2**bits - 1) * step

    return {
        "signal": name,
        "lowest_seen": round(lowest, 4),
        "highest_seen": round(highest, 4),
        "step": step,
        "start": round(start, 4),  # rounding removes tiny float errors, which is safe because the finest step is 0.0001
        "top_it_can_hold": round(top, 4),
        "bits": bits,
    }


if __name__ == "__main__":
    train = pd.read_csv(COMPLETE_TRAINING_DATA_PATH)  # the protocol is designed from training data only

    # Is SPARE_ROOM enough? Check how far "new" training engines go outside the others' ranges.
    worst, worst_signal = largest_overshoot_by_new_engines(train)
    print(f"Worst case over {N_SPLITS} splits: new engines went {worst:.2%} outside the range ({worst_signal})")
    print(f"Spare room used: {SPARE_ROOM:.0%} -> {'enough' if SPARE_ROOM > worst else 'NOT ENOUGH'}")
    print()

    results = pd.DataFrame([design_signal(name, train[name].values) for name in SIGNALS])

    pd.set_option("display.width", 200)  # stop pandas from wrapping the table
    print(results.to_string(index=False))
    print()
    print("total bits:", results["bits"].sum())
    print("Checking the design against the test data is done by the tests: python -m pytest")
