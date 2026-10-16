import socket

import joblib
import pandas as pd

from project_settings import MODEL_PATH
from python_listener.connection import HOST, PORT
from python_listener.row_assembler import RowAssembler


def predict_rul(model, row):
    features = pd.DataFrame([row])[list(model.feature_names_in_)]  # the same columns, in the same order, as in training
    return model.predict(features)[0]


def main():
    assembler = RowAssembler()
    model = joblib.load(MODEL_PATH)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    sock.settimeout(0.5)  # wake up twice a second, so Ctrl+C can stop the program on Windows
    print(f"Listening on {HOST}:{PORT} (Ctrl+C to stop)")

    try:
        while True:
            try:
                packet, _ = sock.recvfrom(65535)  # the largest possible UDP packet, so oversized packets aren't an error
            except TimeoutError:
                continue

            row = assembler.add_packet(packet)
            if row is not None:
                rul = predict_rul(model, row)
                print(f"{row['source_dataset']} engine {row['unit']}, cycle {row['cycle']}: predicted RUL {rul:.1f} cycles")
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
