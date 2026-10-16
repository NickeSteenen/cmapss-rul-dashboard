from pathlib import Path

ROOT = Path(__file__).resolve().parent  # the project folder, regardless of where a script is started from
DATA_DIR = ROOT / "data"

# The raw CMAPSS files have four dataset parts, all with the same 26 columns and no header row
DATASETS = ["FD001", "FD002", "FD003", "FD004"]
COLUMN_NAMES = ["unit", "cycle", "setting1", "setting2", "setting3"] + [f"sensor{i}" for i in range(1, 22)]

COMPLETE_TRAINING_DATA_PATH = DATA_DIR / "complete_training_data.csv"
COMBINED_TEST_DATA_PATH = DATA_DIR / "combined_test_data.csv"  # no RUL column, because the senders read this file
TRUE_RUL_PER_TEST_DATA_CYCLE_PATH = DATA_DIR / "true_rul_per_test_data_cycle.csv"
MODEL_PATH = ROOT / "training" / "rul_model.pkl"
RESULTS_DIR = ROOT / "results"
TEST_SCORES_PATH = RESULTS_DIR / "test_scores.md"
PREDICTED_VS_TRUE_RUL_PLOT_PATH = RESULTS_DIR / "predicted_vs_true_rul.png"
DBC_PATH = ROOT / "protocol" / "cmapss_engine.dbc"
CPP_SENDER_PATH = ROOT / "cpp_sender" / "build" / "Release" / "cmapss_sender.exe"
