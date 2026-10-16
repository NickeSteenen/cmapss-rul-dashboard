import asyncio
import json
import msvcrt
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest
from websockets.asyncio.client import connect

from project_settings import COMBINED_TEST_DATA_PATH, CPP_SENDER_PATH, ROOT
from python_listener.connection import HOST, PORT

BACKEND = "http://127.0.0.1:8000"
needs_cpp_sender = pytest.mark.skipif(not CPP_SENDER_PATH.exists(), reason="the C++ sender isn't built yet")


@pytest.fixture(scope="module", autouse=True)
def backend():
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server:app"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 60  # it loads the 1 GB model first, which takes a few seconds
    while True:
        if process.poll() is not None:
            pytest.fail("The backend didn't start. Another backend, or the listener, already running?")
        try:
            urllib.request.urlopen(f"{BACKEND}/api/status", timeout=1)
            break
        except OSError:
            if time.monotonic() > deadline:
                process.kill()
                pytest.fail("The backend didn't answer within 60 seconds")
            time.sleep(0.5)
    yield
    process.kill()
    process.wait()
    wait_until_udp_port_is_free()


def wait_until_udp_port_is_free():
    # On Windows, the venv's python.exe only starts the real Python as a second program. Stopping it makes the real
    # backend stop too, but a moment later. Wait for that, so the next test file can use port 48000.
    deadline = time.monotonic() + 10
    while True:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.bind((HOST, PORT))
            return
        except OSError:
            if time.monotonic() > deadline:
                pytest.fail(f"The backend still holds port {PORT} 10 seconds after being stopped")
            time.sleep(0.2)
        finally:
            probe.close()


def request(method, path, body=None):
    """Returns the status code and the JSON answer, also when the backend answers with an error code."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{BACKEND}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def collect_live_rows(dataset, unit, number_of_rows):
    """Streams one engine and returns the rows the backend pushes over the WebSocket, like the Live page receives them."""
    async def browser():
        rows = []
        async with connect("ws://127.0.0.1:8000/api/live") as websocket:  # connect first, like the page does
            status, answer = await asyncio.to_thread(
                request, "POST", "/api/start", {"dataset": dataset, "unit": unit, "delay": 0.02})
            assert status == 200, f"Start failed: {answer}"
            while len(rows) < number_of_rows:
                rows.append(json.loads(await asyncio.wait_for(websocket.recv(), timeout=15)))  # fail, don't hang
        return rows

    return asyncio.run(browser())


def wait_until_not_streaming():
    for _ in range(50):
        if not request("GET", "/api/status")[1]["streaming"]:
            return
        time.sleep(0.1)
    pytest.fail("The stream didn't stop within 5 seconds")


@pytest.fixture(autouse=True)
def stop_stream_after_every_test():
    # Runs after every test, even one that failed, so the next test finds nothing streaming
    yield
    request("POST", "/api/stop")


def test_history_returns_every_row_with_true_rul():
    status, rows = request("GET", "/api/history?dataset=FD001&unit=1")

    assert status == 200
    assert [row["cycle"] for row in rows] == list(range(1, 32))  # FD001 engine 1 has 31 cycles, in order
    assert rows[0]["true_rul"] == 142 and rows[-1]["true_rul"] == 112  # worked out from RUL_FD001.txt
    assert all(isinstance(row["predicted_rul"], float) for row in rows)
    assert set(rows[0]) == {"dataset", "unit", "cycle", "predicted_rul", "true_rul", "settings", "sensors"}


def test_history_unknown_dataset_returns_404():
    assert request("GET", "/api/history?dataset=FD005&unit=1")[0] == 404


def test_history_missing_engine_returns_404():
    assert request("GET", "/api/history?dataset=FD001&unit=999")[0] == 404


def test_history_non_numeric_unit_returns_422():
    assert request("GET", "/api/history?dataset=FD001&unit=abc")[0] == 422


def test_engines_returns_every_engine_with_its_cycles():
    status, engines = request("GET", "/api/engines?dataset=FD001")

    assert status == 200
    assert [engine["unit"] for engine in engines] == list(range(1, 101))  # FD001 has 100 test engines
    assert engines[0] == {"unit": 1, "cycles": 31}


def test_engines_unknown_dataset_returns_404():
    assert request("GET", "/api/engines?dataset=FD005")[0] == 404


def test_sensors_returns_names_and_units():
    status, labels = request("GET", "/api/sensors")

    assert status == 200
    assert len(labels) == 21
    assert labels[1] == {"name": "sensor2", "short": "T24", "description": "Total temperature at LPC outlet", "unit": "degR"}


def test_status_without_stream_returns_not_streaming():
    assert request("GET", "/api/status") == (200, {"streaming": False})


def test_start_unknown_dataset_returns_404():
    assert request("POST", "/api/start", {"dataset": "FD005", "unit": 1})[0] == 404


def test_start_missing_engine_returns_404():
    assert request("POST", "/api/start", {"dataset": "FD001", "unit": 999})[0] == 404


def test_start_negative_delay_returns_422():
    assert request("POST", "/api/start", {"dataset": "FD001", "unit": 1, "delay": -1})[0] == 422


@needs_cpp_sender
def test_start_returns_streaming_status():
    assert request("POST", "/api/start", {"dataset": "FD001", "unit": 1, "delay": 0.5}) == (
        200, {"streaming": True, "dataset": "FD001", "unit": 1})
    assert request("GET", "/api/status") == (200, {"streaming": True, "dataset": "FD001", "unit": 1})


@needs_cpp_sender
def test_start_twice_returns_409():
    request("POST", "/api/start", {"dataset": "FD001", "unit": 1, "delay": 0.5})
    assert request("POST", "/api/start", {"dataset": "FD002", "unit": 3})[0] == 409


@needs_cpp_sender
def test_two_simultaneous_starts_return_200_and_409():
    body = {"dataset": "FD001", "unit": 1, "delay": 0.5}
    with ThreadPoolExecutor(max_workers=2) as pool:  # two threads, so both requests reach the backend at the same moment
        answers = list(pool.map(lambda _: request("POST", "/api/start", body), range(2)))
    assert sorted(status for status, _ in answers) == [200, 409]


@needs_cpp_sender
def test_stop_ends_streaming():
    request("POST", "/api/start", {"dataset": "FD001", "unit": 1, "delay": 0.5})
    assert request("POST", "/api/stop") == (200, {"streaming": False})
    assert request("GET", "/api/status") == (200, {"streaming": False})


@needs_cpp_sender
def test_live_sends_every_row_to_the_browser():
    rows = collect_live_rows("FD001", 1, number_of_rows=31)

    assert [row["cycle"] for row in rows] == list(range(1, 32))
    assert all(row["dataset"] == "FD001" and row["unit"] == 1 for row in rows)
    assert rows[0]["true_rul"] == 142 and rows[-1]["true_rul"] == 112
    assert set(rows[0]) == {"dataset", "unit", "cycle", "predicted_rul", "true_rul", "settings", "sensors"}  # same as history


@needs_cpp_sender
def test_live_rows_equal_history_rows():
    # Checks the whole chain at once, from C++ encoding and UDP to decoding, putting rows together, prediction and JSON
    history_rows = request("GET", "/api/history?dataset=FD001&unit=1")[1]
    assert collect_live_rows("FD001", 1, number_of_rows=len(history_rows)) == history_rows


@needs_cpp_sender
def test_stream_ends_by_itself_after_last_row():
    # The live page relies on this. It asks /api/status every second, and enables Start again once the stream has ended.
    assert request("POST", "/api/start", {"dataset": "FD001", "unit": 1, "delay": 0.02})[0] == 200
    wait_until_not_streaming()


@needs_cpp_sender
def test_status_after_sender_fails_includes_error():
    # Lock the start of the data file, the way another program could, so the sender can't read it
    with open(COMBINED_TEST_DATA_PATH, "rb") as data_file:
        msvcrt.locking(data_file.fileno(), msvcrt.LK_NBLCK, 4096)
        try:
            request("POST", "/api/start", {"dataset": "FD001", "unit": 1})
            wait_until_not_streaming()
        finally:
            data_file.seek(0)
            msvcrt.locking(data_file.fileno(), msvcrt.LK_UNLCK, 4096)

    status, answer = request("GET", "/api/status")
    assert status == 200 and answer["streaming"] is False and "error" in answer
