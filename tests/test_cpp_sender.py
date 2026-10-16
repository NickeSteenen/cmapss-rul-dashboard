import socket
import subprocess

import cantools
import pandas as pd
import pytest

from project_settings import COMBINED_TEST_DATA_PATH, CPP_SENDER_PATH, DBC_PATH
from python_listener.connection import HOST, PORT, make_packet


def expected_packets(dataset, unit):
    db = cantools.database.load_file(DBC_PATH)
    messages = sorted(db.messages, key=lambda m: m.frame_id)  # the same order the sender uses
    test = pd.read_csv(COMBINED_TEST_DATA_PATH)
    engine = test[(test["source_dataset"] == dataset) & (test["unit"] == unit)].sort_values("cycle")

    packets = []
    for i, row in enumerate(engine.to_dict("records")):
        values = {**row, "counter": i % 16}
        for message in messages:
            picked = {s.name: values[s.name] for s in message.signals}
            packets.append(make_packet(message.frame_id, message.encode(picked)))
    return packets


@pytest.mark.skipif(not CPP_SENDER_PATH.exists(), reason="the C++ sender isn't built yet (see README, setup step 4)")
@pytest.mark.parametrize("dataset, unit", [("FD001", 1), ("FD004", 7)])
def test_cpp_sender_sends_the_same_packets_as_python(dataset, unit):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1_000_000)  # room to keep every packet until we read them
    try:
        sock.bind((HOST, PORT))
    except OSError:
        sock.close()
        pytest.fail(f"Port {PORT} is already in use. Stop the listener, then run the tests again.")

    try:
        result = subprocess.run(
            [str(CPP_SENDER_PATH), "--dataset", dataset, "--unit", str(unit), "--delay", "0"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"The C++ sender stopped with an error: {result.stderr}"

        received = []
        sock.settimeout(0.5)  # once nothing more arrives for half a second, we have them all
        while True:
            try:
                packet, _ = sock.recvfrom(65535)
            except TimeoutError:
                break
            received.append(packet)
    finally:
        sock.close()

    expected = expected_packets(dataset, unit)
    assert len(received) == len(expected), f"The C++ sender sent {len(received)} packets, Python would send {len(expected)}"
    for i, (got, want) in enumerate(zip(received, expected)):
        assert got == want, f"Packet {i} differs: C++ sent {got.hex(' ')}, Python would send {want.hex(' ')}"


@pytest.mark.skipif(not CPP_SENDER_PATH.exists(), reason="the C++ sender isn't built yet (see README, setup step 4)")
def test_cpp_sender_with_empty_data_file_says_it_could_not_read_the_header(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")

    result = subprocess.run([str(CPP_SENDER_PATH), "--data", str(empty_file)], capture_output=True, text=True, timeout=30)

    assert result.returncode == 1
    assert "header" in result.stderr  # it used to blame a missing column instead
