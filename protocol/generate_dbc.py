import subprocess
import sys

import pandas as pd

from project_settings import COMPLETE_TRAINING_DATA_PATH, DATASETS, DBC_PATH, ROOT
from protocol.compute_signal_ranges import design_signal

C_CODE_DIR = ROOT / "cpp_sender" / "generated"

SENDER = "ENGINE_REPLAY"  # the C++ program that replays the test data
RECEIVER = "RUL_LISTENER"  # the Python program that decodes messages and predicts RUL

# Real names, descriptions and units for each value (from the CMAPSS documentation).
DESCRIPTIONS = {
    "setting1": ("Altitude", "Flight altitude, thousands of feet", "kft"),
    "setting2": ("Mach", "Flight Mach number", ""),
    "setting3": ("TRA", "Throttle resolver angle, power lever position", "%"),
    "sensor1": ("T2", "Total temperature at fan inlet", "degR"),
    "sensor2": ("T24", "Total temperature at LPC outlet", "degR"),
    "sensor3": ("T30", "Total temperature at HPC outlet", "degR"),
    "sensor4": ("T50", "Total temperature at LPT outlet", "degR"),
    "sensor5": ("P2", "Pressure at fan inlet", "psia"),
    "sensor6": ("P15", "Total pressure in bypass duct", "psia"),
    "sensor7": ("P30", "Total pressure at HPC outlet", "psia"),
    "sensor8": ("Nf", "Physical fan speed", "rpm"),
    "sensor9": ("Nc", "Physical core speed", "rpm"),
    "sensor10": ("epr", "Engine pressure ratio, P50/P2", ""),
    "sensor11": ("Ps30", "Static pressure at HPC outlet", "psia"),
    "sensor12": ("phi", "Ratio of fuel flow to Ps30", "pps/psi"),
    "sensor13": ("NRf", "Corrected fan speed", "rpm"),
    "sensor14": ("NRc", "Corrected core speed", "rpm"),
    "sensor15": ("BPR", "Bypass ratio", ""),
    "sensor16": ("farB", "Burner fuel-air ratio", ""),
    "sensor17": ("htBleed", "Bleed enthalpy", ""),
    "sensor18": ("Nf_dmd", "Demanded fan speed", "rpm"),
    "sensor19": ("PCNfR_dmd", "Demanded corrected fan speed", "%"),  # published table says rpm, but values are 84.93-100
    "sensor20": ("W31", "HPT coolant bleed", "lbm/s"),
    "sensor21": ("W32", "LPT coolant bleed", "lbm/s"),
}

# Values whose size we chose ourselves, instead of calculating from the data (they are counts, not measurements).
FIXED_SIGNALS = {
    "counter": {"bits": 4, "unit": "", "comment": "Row counter. Counts 0-15, then starts over at 0. All six messages of one row carry the same value"},
    "source_dataset": {"bits": 2, "unit": "", "comment": "Which CMAPSS dataset the engine comes from"},
    "unit": {"bits": 9, "unit": "", "comment": "Engine number within its dataset"},
    "cycle": {"bits": 10, "unit": "cycles", "comment": "Flight number of this engine"},
}

# The six messages, each with its ID, name, description and the values inside (the counter is added first automatically).
MESSAGES = [
    (0x100, "ENGINE_INFO", "Which engine and flight this row is, and the flight conditions",
     ["source_dataset", "unit", "cycle", "setting1", "setting2", "setting3"]),
    (0x101, "SENSORS_1", "Sensors 1-4", ["sensor1", "sensor2", "sensor3", "sensor4"]),
    (0x102, "SENSORS_2", "Sensors 5-8", ["sensor5", "sensor6", "sensor7", "sensor8"]),
    (0x103, "SENSORS_3", "Sensors 9-12", ["sensor9", "sensor10", "sensor11", "sensor12"]),
    (0x104, "SENSORS_4", "Sensors 13-17", ["sensor13", "sensor14", "sensor15", "sensor16", "sensor17"]),
    (0x105, "SENSORS_5", "Sensors 18-21", ["sensor18", "sensor19", "sensor20", "sensor21"]),
]


def dbc_number(x):
    return f"{x:.4f}".rstrip("0").rstrip(".")  # 0.0100 -> 0.01, 56.0000 -> 56


def build_signal(name, train):
    if name in FIXED_SIGNALS:
        fixed = FIXED_SIGNALS[name]
        return {"name": name, "bits": fixed["bits"], "step": 1, "start": 0,
                "top": 2 ** fixed["bits"] - 1, "unit": fixed["unit"], "comment": fixed["comment"]}
    design = design_signal(name, train[name].values)
    short, description, unit = DESCRIPTIONS[name]
    return {"name": name, "bits": design["bits"], "step": design["step"], "start": design["start"],
            "top": design["top_it_can_hold"], "unit": unit, "comment": f"{short}: {description}"}


def build_messages(train):
    messages = []
    for msg_id, msg_name, msg_comment, value_names in MESSAGES:
        position = 0
        signals = []
        for name in ["counter"] + value_names:  # the counter always goes first, in bits 0-3
            signal = build_signal(name, train)
            signal["position"] = position
            position += signal["bits"]
            signals.append(signal)
        if position > 64:
            raise ValueError(f"{msg_name} needs {position} bits, but a message only holds 64")
        messages.append({"id": msg_id, "name": msg_name, "comment": msg_comment, "signals": signals})
    return messages


def dbc_text(messages):
    lines = [
        'VERSION ""',
        "",
        "",
        "NS_ :",  # a fixed list of keywords that every DBC file starts with, which tools expect
        *[f"\t{keyword}" for keyword in [
            "NS_DESC_", "CM_", "BA_DEF_", "BA_", "VAL_", "CAT_DEF_", "CAT_", "FILTER", "BA_DEF_DEF_",
            "EV_DATA_", "ENVVAR_DATA_", "SGTYPE_", "SGTYPE_VAL_", "BA_DEF_SGTYPE_", "BA_SGTYPE_",
            "SIG_TYPE_REF_", "VAL_TABLE_", "SIG_GROUP_", "SIG_VALTYPE_", "SIGTYPE_VALTYPE_", "BO_TX_BU_",
            "BA_DEF_REL_", "BA_REL_", "BA_DEF_DEF_REL_", "BU_SG_REL_", "BU_EV_REL_", "BU_BO_REL_", "SG_MUL_VAL_"]],
        "",
        "BS_:",  # bus speed, left empty since there is no real bus
        "",
        f"BU_: {SENDER} {RECEIVER}",  # the nodes on the network
        "",
    ]

    for msg in messages:
        lines.append("")
        lines.append(f"BO_ {msg['id']} {msg['name']}: 8 {SENDER}")  # message: decimal ID, name, 8 bytes, sender
        for s in msg["signals"]:
            lines.append(  # signal: position|bits, @1+ = Intel byte order and unsigned, (step,start), [start|top], unit, receiver
                f" SG_ {s['name']} : {s['position']}|{s['bits']}@1+ ({dbc_number(s['step'])},{dbc_number(s['start'])}) "
                f"[{dbc_number(s['start'])}|{dbc_number(s['top'])}] \"{s['unit']}\" {RECEIVER}"
            )

    lines.append("")
    lines.append("")
    lines.append(f'CM_ BU_ {SENDER} "Replays CMAPSS test data as CAN messages";')
    lines.append(f'CM_ BU_ {RECEIVER} "Decodes messages and predicts remaining useful life";')
    for msg in messages:
        lines.append(f'CM_ BO_ {msg["id"]} "{msg["comment"]}";')
        for s in msg["signals"]:
            lines.append(f'CM_ SG_ {msg["id"]} {s["name"]} "{s["comment"]}";')

    info_id = next(m["id"] for m in messages if any(s["name"] == "source_dataset" for s in m["signals"]))
    choices = " ".join(f'{i} "{name}"' for i, name in enumerate(DATASETS))  # 0 "FD001" 1 "FD002" ...
    lines.append(f"VAL_ {info_id} source_dataset {choices} ;")  # value table: which number means which dataset
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    train = pd.read_csv(COMPLETE_TRAINING_DATA_PATH)  # the protocol is designed from training data only
    messages = build_messages(train)
    DBC_PATH.write_text(dbc_text(messages), encoding="ascii")
    print(f"Wrote {DBC_PATH}")
    for msg in messages:
        used = sum(s["bits"] for s in msg["signals"])
        print(f"  {hex(msg['id'])} {msg['name']}: {used}/64 bits used")

    C_CODE_DIR.mkdir(exist_ok=True)
    subprocess.run(  # --use-round: round values to the nearest step instead of cutting off decimals
        [sys.executable, "-m", "cantools", "generate_c_source", "--use-round", str(DBC_PATH), "-o", str(C_CODE_DIR)],
        check=True, capture_output=True,
    )
    print(f"Wrote C code for the C++ sender to {C_CODE_DIR}")
    print("Now run the tests to check it: python -m pytest")
