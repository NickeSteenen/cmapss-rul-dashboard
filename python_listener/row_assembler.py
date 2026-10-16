import math

import cantools

from project_settings import DBC_PATH
from python_listener.connection import PACKET_SIZE, split_packet


def decimals_in(step):
    """0.01 -> 2, 1 -> 0. Every step in the DBC file is a power of ten."""
    return max(0, round(-math.log10(step)))


class RowAssembler:
    """Puts incoming packets back together into complete rows. Six messages with the same counter make one row."""

    def __init__(self):
        self.db = cantools.database.load_file(DBC_PATH)
        self.decimals = {signal.name: decimals_in(signal.scale) for message in self.db.messages for signal in message.signals}
        self.messages_per_row = len(self.db.messages)
        self.ignored_packets = 0
        self.dropped_rows = 0
        self._start_new_row(None)

    def _start_new_row(self, counter):
        self.row = {}
        self.row_counter = counter
        self.received_ids = set()

    def add_packet(self, packet):
        """Takes one packet. Returns the complete row once all six messages have arrived, otherwise None."""
        frame = split_packet(packet)
        if frame is None:
            self.ignored_packets += 1
            print(f"  Ignored a {len(packet)}-byte packet (ours are {PACKET_SIZE} bytes)")
            return None
        frame_id, data = frame

        try:
            message = self.db.get_message_by_frame_id(frame_id)
        except KeyError:
            self.ignored_packets += 1
            print(f"  Ignored a packet with unknown ID {hex(frame_id)}")
            return None
        values = message.decode(data)
        # Decoding multiplies by the step, which leaves noise like 14.620000000000001 instead of 14.62
        values = {name: round(value, self.decimals[name]) if isinstance(value, float) else value
                  for name, value in values.items()}

        new_row_started = values["counter"] != self.row_counter
        if new_row_started:
            if self.received_ids:
                self.dropped_rows += 1
                print(f"  Dropped incomplete row (counter {self.row_counter}): "
                      f"only {len(self.received_ids)} of {self.messages_per_row} messages arrived")
            self._start_new_row(values["counter"])

        self.row.update(values)
        self.received_ids.add(frame_id)

        if len(self.received_ids) == self.messages_per_row:
            complete_row = self.row
            self._start_new_row(None)
            return complete_row
        return None
