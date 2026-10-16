import cantools
import pandas as pd
import pytest

from project_settings import COMBINED_TEST_DATA_PATH, DBC_PATH

TOLERANCE = 1e-6  # real mistakes are at least one step (0.0001 or more)


@pytest.fixture(scope="module")
def db():
    return cantools.database.load_file(DBC_PATH)  # loading also fails if the file is broken, e.g. two values overlapping


@pytest.fixture(scope="module")
def test_rows():
    return pd.read_csv(COMBINED_TEST_DATA_PATH).to_dict("records")


def test_every_test_row_comes_back_exactly(db, test_rows):
    for i, row in enumerate(test_rows):
        values = {**row, "counter": i % 16}
        for msg in db.messages:
            sent = {s.name: values[s.name] for s in msg.signals}
            received = msg.decode(msg.encode(sent))
            for name, value in sent.items():
                got = received[name]
                if name == "source_dataset":  # comes back as text ("FD001") through the value table
                    assert str(got) == value, f"Test row {i}: {name} was sent as {value} but came back as {got}"
                else:
                    assert abs(got - value) <= TOLERANCE, f"Test row {i}: {name} was sent as {value} but came back as {got}"


def test_lowest_and_highest_allowed_values_come_back_exactly(db):
    for msg in db.messages:
        for edge in ("minimum", "maximum"):
            sent = {s.name: getattr(s, edge) for s in msg.signals}  # the [start|top] numbers written in the DBC file
            received = msg.decode(msg.encode(sent), decode_choices=False)  # source_dataset as a number, not "FD001"
            for name, value in sent.items():
                got = received[name]
                assert abs(got - value) <= TOLERANCE, f"{msg.name}: {name} at its {edge} was sent as {value} but came back as {got}"
