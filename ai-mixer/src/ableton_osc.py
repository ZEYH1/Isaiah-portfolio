"""OSC client for AbletonOSC.

AbletonOSC listens on UDP port 11000 by default and sends back on 11001.
See https://github.com/ideoforms/AbletonOSC for the full address space.
"""

from pythonosc.udp_client import SimpleUDPClient

DEFAULT_HOST = "127.0.0.1"
DEFAULT_SEND_PORT = 11000


class AbletonClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_SEND_PORT):
        self.client = SimpleUDPClient(host, port)

    def set_track_volume(self, track_index: int, volume: float) -> None:
        self.client.send_message("/live/track/set/volume", [track_index, volume])

    def set_track_panning(self, track_index: int, pan: float) -> None:
        self.client.send_message("/live/track/set/panning", [track_index, pan])

    def set_device_parameter(
        self, track_index: int, device_index: int, parameter_index: int, value: float
    ) -> None:
        self.client.send_message(
            "/live/device/set/parameter/value",
            [track_index, device_index, parameter_index, value],
        )
