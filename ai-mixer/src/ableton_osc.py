"""OSC client for AbletonOSC.

AbletonOSC listens for commands on UDP port 11000 and sends replies
back on port 11001. See https://github.com/ideoforms/AbletonOSC for
the address space.
"""

from __future__ import annotations

import threading
import time

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


DEFAULT_HOST = "127.0.0.1"
DEFAULT_SEND_PORT = 11000
DEFAULT_RECV_PORT = 11001

# Live's track volume fader is non-linear, but near unity 1 dB ~= 0.025 of the
# normalized 0.0-1.0 fader range. Good enough for small deltas.
DB_PER_FADER_UNIT = 1.0 / 0.025


class AbletonClient:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        send_port: int = DEFAULT_SEND_PORT,
        recv_port: int = DEFAULT_RECV_PORT,
    ):
        self.client = SimpleUDPClient(host, send_port)
        self._latest: dict[str, tuple] = {}
        self._lock = threading.Lock()
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._on_message)
        self._server = ThreadingOSCUDPServer(("0.0.0.0", recv_port), dispatcher)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()

    def _on_message(self, address: str, *args) -> None:
        with self._lock:
            self._latest[address] = args

    def _query(self, address: str, send_args: list | None = None, timeout: float = 2.0):
        with self._lock:
            self._latest.pop(address, None)
        self.client.send_message(address, send_args or [])
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if address in self._latest:
                    return self._latest[address]
            time.sleep(0.01)
        raise TimeoutError(f"No reply from Ableton for {address} within {timeout}s")

    # ----- Tracks -----

    def get_track_names(self) -> list[str]:
        reply = self._query("/live/song/get/track_names")
        return [str(name) for name in reply]

    def get_track_volume(self, track_index: int) -> float:
        reply = self._query("/live/track/get/volume", [track_index])
        return float(reply[-1])

    def get_track_panning(self, track_index: int) -> float:
        reply = self._query("/live/track/get/panning", [track_index])
        return float(reply[-1])

    def set_track_volume(self, track_index: int, volume: float) -> None:
        self.client.send_message("/live/track/set/volume", [track_index, float(volume)])

    def set_track_panning(self, track_index: int, pan: float) -> None:
        self.client.send_message("/live/track/set/panning", [track_index, float(pan)])

    # ----- Devices -----

    def get_track_device_names(self, track_index: int) -> list[str]:
        reply = self._query("/live/track/get/devices/name", [track_index])
        return [str(n) for n in reply]

    def get_track_device_class_names(self, track_index: int) -> list[str]:
        reply = self._query("/live/track/get/devices/class_name", [track_index])
        return [str(n) for n in reply]

    def get_device_parameter_names(self, track_index: int, device_index: int) -> list[str]:
        reply = self._query(
            "/live/device/get/parameters/name", [track_index, device_index]
        )
        return [str(n) for n in reply]

    def get_device_parameter_values(self, track_index: int, device_index: int) -> list[float]:
        reply = self._query(
            "/live/device/get/parameters/value", [track_index, device_index]
        )
        return [float(v) for v in reply]

    def set_device_parameter(
        self, track_index: int, device_index: int, parameter_index: int, value: float
    ) -> None:
        self.client.send_message(
            "/live/device/set/parameter/value",
            [track_index, device_index, parameter_index, float(value)],
        )

    # ----- Return tracks -----

    def get_return_track_names(self) -> list[str]:
        reply = self._query("/live/song/get/return_track_names")
        return [str(n) for n in reply]

    def get_return_device_class_names(self, return_index: int) -> list[str]:
        reply = self._query(
            "/live/return_track/get/devices/class_name", [return_index]
        )
        return [str(n) for n in reply]

    def get_return_device_parameter_names(
        self, return_index: int, device_index: int
    ) -> list[str]:
        reply = self._query(
            "/live/return_track/device/get/parameters/name",
            [return_index, device_index],
        )
        return [str(n) for n in reply]

    def set_return_device_parameter(
        self,
        return_index: int,
        device_index: int,
        parameter_index: int,
        value: float,
    ) -> None:
        self.client.send_message(
            "/live/return_track/device/set/parameter/value",
            [return_index, device_index, parameter_index, float(value)],
        )

    # ----- Sends -----

    def get_track_send(self, track_index: int, send_index: int) -> float:
        reply = self._query("/live/track/get/send", [track_index, send_index])
        return float(reply[-1])

    def set_track_send(self, track_index: int, send_index: int, value: float) -> None:
        self.client.send_message(
            "/live/track/set/send",
            [track_index, send_index, float(value)],
        )


def db_to_fader_delta(delta_db: float) -> float:
    """Approximate dB delta -> linear fader delta near unity gain."""
    return delta_db / DB_PER_FADER_UNIT
