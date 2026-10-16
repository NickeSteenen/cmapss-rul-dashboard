import asyncio
import subprocess
import threading
from contextlib import asynccontextmanager

import cantools
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from project_settings import (
    COMBINED_TEST_DATA_PATH,
    CPP_SENDER_PATH,
    DATASETS,
    DBC_PATH,
    MODEL_PATH,
    TRUE_RUL_PER_TEST_DATA_CYCLE_PATH,
)
from python_listener.connection import HOST, PORT
from python_listener.listener import predict_rul
from python_listener.row_assembler import RowAssembler

SETTINGS = ["setting1", "setting2", "setting3"]
SENSORS = [f"sensor{i}" for i in range(1, 22)]

# Loaded once, when the server starts. The model file is 1 GB, so this takes a few seconds.
model = joblib.load(MODEL_PATH)
test_data = pd.read_csv(COMBINED_TEST_DATA_PATH)
true_rul_per_test_data_cycle = pd.read_csv(TRUE_RUL_PER_TEST_DATA_CYCLE_PATH)
true_rul_lookup = {
    (r.source_dataset, int(r.unit), int(r.cycle)): int(r.RUL) for r in true_rul_per_test_data_cycle.itertuples()
}

def read_sensor_labels():
    """Every sensor's real name, description and unit, from the comments and units in the DBC file."""
    labels = []
    for message in cantools.database.load_file(DBC_PATH).messages:
        for signal in message.signals:
            if signal.name.startswith("sensor"):
                short, description = signal.comment.split(": ", 1)  # "T24: Total temperature at LPC outlet"
                labels.append({"name": signal.name, "short": short, "description": description, "unit": signal.unit})
    return labels


sensor_labels = read_sensor_labels()

live_clients = set()
live_rows = asyncio.Queue()


def make_json_row_for_browser(dataset, unit, cycle, predicted_rul, true_rul, values):
    """One row, the way the frontend gets it. History and live rows both use this, so they always look the same."""
    return {
        "dataset": dataset,
        "unit": int(unit),
        "cycle": int(cycle),
        "predicted_rul": float(predicted_rul),
        "true_rul": None if true_rul is None else int(true_rul),
        "settings": {name: float(values[name]) for name in SETTINGS},
        "sensors": {name: float(values[name]) for name in SENSORS},
    }


def check_dataset_exists(dataset):
    if dataset not in DATASETS:
        raise HTTPException(status_code=404, detail=f"dataset must be one of {', '.join(DATASETS)}")


def find_engine(dataset, unit):
    """One engine's test rows. Answers the request with an error if the dataset or engine doesn't exist."""
    check_dataset_exists(dataset)
    engine = test_data[(test_data["source_dataset"] == dataset) & (test_data["unit"] == unit)]
    if engine.empty:
        raise HTTPException(status_code=404, detail=f"No rows for {dataset} engine {unit}")
    return engine


class PacketReceiver(asyncio.DatagramProtocol):
    """Receives the senders' UDP packets. The event loop calls datagram_received for every packet that arrives."""

    def __init__(self):
        self.assembler = RowAssembler()

    def datagram_received(self, data, addr):
        row = self.assembler.add_packet(data)
        if row is None:
            return
        dataset, unit, cycle = str(row["source_dataset"]), row["unit"], row["cycle"]
        predicted_rul = predict_rul(model, row)
        true_rul = true_rul_lookup.get((dataset, unit, cycle))  # only used for showing, never given to the model
        live_rows.put_nowait(make_json_row_for_browser(dataset, unit, cycle, predicted_rul, true_rul, row))
        print(f"Live: {dataset} engine {unit}, cycle {cycle}: predicted RUL {predicted_rul:.1f}, true RUL {true_rul}")


class CppSender:
    """Starts and stops the C++ sender, and knows whether it's running."""

    def __init__(self):
        self.process = None
        self.engine = None
        self.stopped_by_user = False
        self.error_message = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, dataset, unit, delay):
        self.process = subprocess.Popen(
            [str(CPP_SENDER_PATH), "--dataset", dataset, "--unit", str(unit), "--delay", str(delay),
             "--data", str(COMBINED_TEST_DATA_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.engine = (dataset, unit)
        self.stopped_by_user = False
        self.error_message = None

    def stop(self):
        if self.is_running():
            self.stopped_by_user = True  # terminate() also gives an error exit code, which isn't a real error
            self.process.terminate()
            self.process.wait(timeout=5)

    def status(self):
        if self.is_running():
            return {"streaming": True, "dataset": self.engine[0], "unit": self.engine[1]}
        if self.ended_with_error():
            return {"streaming": False, "error": self.read_error_message()}
        return {"streaming": False}

    def ended_with_error(self):
        return self.process is not None and self.process.returncode != 0 and not self.stopped_by_user

    def read_error_message(self):
        if self.error_message is None:  # the sender's error output can only be read once, so keep it
            text = self.process.stderr.read().strip().removeprefix("Error: ")
            self.error_message = text or f"Exited with code {self.process.returncode}"
        return self.error_message


packet_receiver = PacketReceiver()
cpp_sender = CppSender()
sender_lock = threading.Lock()  # FastAPI runs requests in parallel threads, so this lets one request at a time use the sender


@asynccontextmanager
async def lifespan(app):
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(lambda: packet_receiver, local_addr=(HOST, PORT))
    sender_task = asyncio.create_task(send_live_rows())
    print(f"Listening for packets on {HOST}:{PORT}")
    yield
    cpp_sender.stop()
    sender_task.cancel()
    transport.close()


async def send_live_rows():
    """Takes the rows out of the queue, in order, and sends each one to every connected browser."""
    while True:
        message = await live_rows.get()
        for websocket in list(live_clients):
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"  Stopped sending to a browser: {e!r}")
                live_clients.discard(websocket)


app = FastAPI(lifespan=lifespan)


@app.get("/api/history")
def history(dataset: str, unit: int):
    engine = find_engine(dataset, unit)
    engine = engine.merge(true_rul_per_test_data_cycle, on=["source_dataset", "unit", "cycle"]).sort_values("cycle")
    predictions = model.predict(engine[list(model.feature_names_in_)])

    return [
        make_json_row_for_browser(dataset, unit, row["cycle"], predicted_rul, row["RUL"], row)
        for row, predicted_rul in zip(engine.to_dict("records"), predictions)
    ]


@app.get("/api/engines")
def engines(dataset: str):
    check_dataset_exists(dataset)
    cycles_per_engine = test_data[test_data["source_dataset"] == dataset].groupby("unit")["cycle"].count()
    return [{"unit": int(unit), "cycles": int(cycles)} for unit, cycles in cycles_per_engine.items()]


@app.get("/api/sensors")
def sensors():
    return sensor_labels


class StartRequest(BaseModel):
    dataset: str
    unit: int
    delay: float = Field(default=0.5, ge=0, allow_inf_nan=False)  # seconds between cycles


@app.post("/api/start")
def start(request: StartRequest):
    find_engine(request.dataset, request.unit)
    if not CPP_SENDER_PATH.exists():
        raise HTTPException(status_code=500, detail="The C++ sender isn't built yet (see README, setup step 4)")

    with sender_lock:
        if cpp_sender.is_running():
            dataset, unit = cpp_sender.engine
            raise HTTPException(status_code=409, detail=f"Already streaming {dataset} engine {unit}. Stop it first.")
        packet_receiver.assembler = RowAssembler()  # forget any half-finished row left over from an earlier stream
        cpp_sender.start(request.dataset, request.unit, request.delay)
        return cpp_sender.status()


@app.post("/api/stop")
def stop():
    with sender_lock:
        cpp_sender.stop()
        return cpp_sender.status()


@app.get("/api/status")
def status():
    with sender_lock:
        return cpp_sender.status()


@app.websocket("/api/live")
async def live(websocket: WebSocket):
    await websocket.accept()
    live_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # the browser never sends anything, so this just waits until it disconnects
    except WebSocketDisconnect:
        pass
    finally:
        live_clients.discard(websocket)
