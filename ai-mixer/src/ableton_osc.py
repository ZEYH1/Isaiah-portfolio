"""OSC client for AbletonOSC.

AbletonOSC listens for commands on UDP port 11000 and sends replies
back on port 11001. See https://github.com/ideoforms/AbletonOSC for
the address space.

In addition to the basic track / device / send accessors, this module
exposes higher-level apply_sidechain() and apply_transient() helpers
used by the new sidechain and transient action types.
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

    def find_device_index(
        self, track_index: int, name_or_class_substr: str
    ) -> int | None:
        """Return the index of the first device on a track whose display name
        or class name contains the given substring (case-insensitive)."""
        needle = name_or_class_substr.lower()
        try:
            names = self.get_track_device_names(track_index)
        except TimeoutError:
            names = []
        for i, n in enumerate(names):
            if needle in n.lower():
                return i
        try:
            class_names = self.get_track_device_class_names(track_index)
        except TimeoutError:
            class_names = []
        for i, n in enumerate(class_names):
            if needle in n.lower():
                return i
        return None

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

    # ----- Sidechain (Phase 2) -----

    def apply_sidechain(self, suggestion: dict, track_names: list[str]) -> dict:
        """Configure sidechain compression: trigger_track -> target_track.

        Strategy:
          1. Find the Compressor on the target track.
          2. Push threshold / ratio / attack / release values into it.
          3. Best-effort attempt to flip a 'sidechain on' parameter if the
             compressor exposes one by that name; otherwise return a partial-
             status dict instructing the user to verify the audio routing
             manually in Live's compressor UI.

        AbletonOSC does not expose sidechain audio routing across all
        versions, so the audio source step is intentionally manual.
        """
        trigger_track = suggestion["trigger_track"]
        target_track = suggestion["target_track"]

        trigger_idx = None
        target_idx = None
        for i, name in enumerate(track_names):
            if name == trigger_track:
                trigger_idx = i
            if name == target_track:
                target_idx = i

        if trigger_idx is None or target_idx is None:
            return {
                "status": "error",
                "message": (
                    f"Could not find tracks: '{trigger_track}' / '{target_track}'"
                ),
            }

        device_index = self.find_device_index(target_idx, "Compressor")
        if device_index is None:
            return {
                "status": "warning",
                "message": (
                    f"No Compressor found on '{target_track}'. Add one then re-apply."
                ),
                "manual_steps": [
                    f"Add Ableton Compressor to '{target_track}'",
                    f"Enable Sidechain, set Audio From to '{trigger_track}'",
                    f"Threshold: {suggestion.get('threshold_db', -20)} dB",
                    f"Ratio: {suggestion.get('ratio', 8)}:1",
                    f"Attack: {suggestion.get('attack_ms', 1)} ms",
                    f"Release: {suggestion.get('release_ms', 150)} ms",
                ],
            }

        param_names = self.get_device_parameter_names(target_idx, device_index)

        # Map suggestion fields -> Ableton parameter names (Compressor / Compressor2)
        targets: dict[str, float] = {
            "Threshold": float(suggestion.get("threshold_db", -20.0)),
            "Ratio": float(suggestion.get("ratio", 8.0)),
            "Attack Time": float(suggestion.get("attack_ms", 1.0)) / 1000.0,
            "Release Time": float(suggestion.get("release_ms", 150.0)) / 1000.0,
        }
        applied: dict[str, float] = {}
        for i, p_name in enumerate(param_names):
            if p_name in targets:
                self.set_device_parameter(target_idx, device_index, i, targets[p_name])
                applied[p_name] = targets[p_name]

        # Best-effort: flip a "sidechain on" style toggle if present
        for i, p_name in enumerate(param_names):
            lower = p_name.lower()
            if "sidechain" in lower and ("on" in lower or "enable" in lower):
                self.set_device_parameter(target_idx, device_index, i, 1.0)
                applied[p_name] = 1.0
                break

        return {
            "status": "partial",
            "message": (
                f"Compressor dynamics set on '{target_track}'. "
                f"Verify Sidechain -> Audio From is set to '{trigger_track}' "
                f"in Live's compressor UI."
            ),
            "values_applied": applied,
        }

    # ----- Transient shaper (Phase 2) -----

    def apply_transient(self, suggestion: dict, track_names: list[str]) -> dict:
        """Apply transient shaping via Ableton's native Transient Shaper.

        Falls back to manual instructions if no Transient Shaper is found
        on the track.
        """
        track_name = suggestion["track"]
        track_idx = None
        for i, name in enumerate(track_names):
            if name == track_name:
                track_idx = i
                break

        if track_idx is None:
            return {"status": "error", "message": f"Track '{track_name}' not found"}

        device_index = self.find_device_index(track_idx, "TransientShaper")
        if device_index is None:
            return {
                "status": "warning",
                "message": (
                    f"No Transient Shaper found on '{track_name}'. Add one manually."
                ),
                "manual_steps": [
                    f"Add Ableton Transient Shaper to '{track_name}'",
                    f"Set Attack to {suggestion.get('attack_delta_db', 0):+.1f} dB",
                    f"Set Sustain to {suggestion.get('sustain_delta_db', 0):+.1f} dB",
                ],
            }

        param_names = self.get_device_parameter_names(track_idx, device_index)
        targets: dict[str, float] = {
            "Attack": float(suggestion.get("attack_delta_db", 0.0)),
            "Sustain": float(suggestion.get("sustain_delta_db", 0.0)),
        }
        applied: dict[str, float] = {}
        for i, p_name in enumerate(param_names):
            if p_name in targets:
                clamped = max(-12.0, min(12.0, targets[p_name]))
                self.set_device_parameter(track_idx, device_index, i, clamped)
                applied[p_name] = clamped

        return {
            "status": "ok",
            "message": f"Transient shaper applied to '{track_name}'",
            "values_applied": applied,
        }


def db_to_fader_delta(delta_db: float) -> float:
    """Approximate dB delta -> linear fader delta near unity gain."""
    return delta_db / DB_PER_FADER_UNIT
