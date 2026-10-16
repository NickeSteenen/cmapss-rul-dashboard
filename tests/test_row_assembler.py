import cantools
import pandas as pd
import pytest

from project_settings import COLUMN_NAMES, COMBINED_TEST_DATA_PATH, DBC_PATH
from python_listener.connection import make_packet
from python_listener.row_assembler import RowAssembler

DB = cantools.database.load_file(DBC_PATH)
MESSAGES = sorted(DB.messages, key=lambda m: m.frame_id)


@pytest.fixture(scope="module")
def rows():
    test = pd.read_csv(COMBINED_TEST_DATA_PATH)
    engine = test[(test["source_dataset"] == "FD001") & (test["unit"] == 1)].sort_values("cycle")
    return engine.head(2).to_dict("records")


def packets_for(row, counter):
    values = {**row, "counter": counter}
    return [make_packet(m.frame_id, m.encode({s.name: values[s.name] for s in m.signals})) for m in MESSAGES]


def test_a_row_comes_out_once_all_six_messages_have_arrived(rows):
    assembler = RowAssembler()
    results = [assembler.add_packet(p) for p in packets_for(rows[0], counter=0)]

    assert results[:5] == [None] * 5
    row = results[5]
    assert row["cycle"] == rows[0]["cycle"]
    assert abs(row["sensor1"] - rows[0]["sensor1"]) < 1e-6
    assert abs(row["sensor21"] - rows[0]["sensor21"]) < 1e-6


def test_decoded_values_are_exactly_the_csv_values(rows):
    assembler = RowAssembler()
    for counter, csv_row in enumerate(rows):
        row = [assembler.add_packet(p) for p in packets_for(csv_row, counter)][5]
        for name in COLUMN_NAMES:
            assert row[name] == csv_row[name], f"{name}: decoded {row[name]!r}, CSV {csv_row[name]!r}"


def test_the_messages_of_a_row_can_arrive_in_any_order(rows):
    assembler = RowAssembler()
    results = [assembler.add_packet(p) for p in reversed(packets_for(rows[0], counter=0))]

    assert results[:5] == [None] * 5
    assert results[5]["cycle"] == rows[0]["cycle"]


def test_an_incomplete_row_is_dropped_when_the_next_row_starts(rows):
    assembler = RowAssembler()
    first_row = packets_for(rows[0], counter=0)
    del first_row[3]  # SENSORS_3 of the first row never arrives

    for p in first_row:
        assert assembler.add_packet(p) is None
    results = [assembler.add_packet(p) for p in packets_for(rows[1], counter=1)]

    assert assembler.dropped_rows == 1
    row = results[5]
    assert row["cycle"] == rows[1]["cycle"]
    assert abs(row["sensor9"] - rows[1]["sensor9"]) < 1e-6  # its own SENSORS_3 values, not mixed with the first row's


def test_packets_that_are_not_ours_are_ignored(rows):
    assembler = RowAssembler()

    assert assembler.add_packet(b"x" * 20) is None
    assert assembler.add_packet(make_packet(0x7FF, bytes(8))) is None  # right size, but an ID that isn't in the DBC file
    assert assembler.ignored_packets == 2

    results = [assembler.add_packet(p) for p in packets_for(rows[0], counter=0)]
    assert results[5]["cycle"] == rows[0]["cycle"]  # real packets still work afterwards
