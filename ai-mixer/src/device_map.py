"""Translates semantic mixing actions into the right OSC device parameter calls.

Phase 1 covers Ableton stock devices (EQ Eight, Compressor, Reverb, Echo)
and the return-track template documented in template/AI_Mixer_Template_Setup.md.

The lookup strategy is name-based, not index-based, so it survives Live
version changes that shift device class layouts.
"""

from __future__ import annotations

from ableton_osc import AbletonClient


# Names of the return tracks the assistant expects (must match the template).
RETURN_PARALLEL_COMP = "Parallel Comp"
RETURN_PLATE_REVERB = "Plate Reverb"
RETURN_HALL_REVERB = "Hall Reverb"
RETURN_SLAP = "1/8 Slap"
RETURN_DOTTED = "1/4 Dotted"

# Class names for stock devices we care about.
EQ_EIGHT_CLASS = "Eq8"
COMPRESSOR_CLASS = "Compressor2"
REVERB_CLASS = "Reverb"
ECHO_CLASS = "Echo"


def _find_device_by_class(
    client: AbletonClient, track_index: int, class_name: str
) -> int | None:
    """Return the device index of the first device matching the class on a track."""
    try:
        classes = client.get_track_device_class_names(track_index)
    except Exception:
        return None
    for i, cls in enumerate(classes):
        if cls == class_name:
            return i
    return None


def _find_param(names: list[str], wanted: str) -> int | None:
    """Find a parameter index by exact name, then by case-insensitive contains."""
    for i, n in enumerate(names):
        if n == wanted:
            return i
    wanted_lower = wanted.lower()
    for i, n in enumerate(names):
        if wanted_lower in n.lower():
            return i
    return None


# ----- Return tracks -----


def find_return_index(client: AbletonClient, return_name: str) -> int | None:
    try:
        names = client.get_return_track_names()
    except Exception:
        return None
    target = return_name.strip().lower()
    for i, n in enumerate(names):
        if n.strip().lower() == target:
            return i
    return None


# ----- EQ Eight -----


def set_eq_band(
    client: AbletonClient,
    track_index: int,
    band: int,
    *,
    freq_hz: float | None = None,
    gain_db: float | None = None,
    q: float | None = None,
    enable: bool | None = None,
) -> dict:
    """Apply an EQ band move on the first EQ Eight on the given track.

    Returns a dict describing what changed (or skipped, with reason).
    `band` is 1-8.
    """
    if not (1 <= band <= 8):
        return {"ok": False, "reason": f"band {band} out of range (1-8)"}

    device_index = _find_device_by_class(client, track_index, EQ_EIGHT_CLASS)
    if device_index is None:
        return {"ok": False, "reason": "no EQ Eight found on track"}

    names = client.get_device_parameter_names(track_index, device_index)
    changed: dict[str, float] = {}

    if enable is not None:
        idx = _find_param(names, f"{band} Filter On A")
        if idx is not None:
            client.set_device_parameter(track_index, device_index, idx, 1.0 if enable else 0.0)
            changed["enabled"] = 1.0 if enable else 0.0

    if freq_hz is not None:
        idx = _find_param(names, f"{band} Frequency A")
        if idx is not None:
            v = max(20.0, min(22000.0, float(freq_hz)))
            client.set_device_parameter(track_index, device_index, idx, v)
            changed["freq_hz"] = v

    if gain_db is not None:
        idx = _find_param(names, f"{band} Gain A")
        if idx is not None:
            v = max(-15.0, min(15.0, float(gain_db)))
            client.set_device_parameter(track_index, device_index, idx, v)
            changed["gain_db"] = v

    if q is not None:
        idx = _find_param(names, f"{band} Resonance A")
        if idx is not None:
            v = max(0.1, min(18.0, float(q)))
            client.set_device_parameter(track_index, device_index, idx, v)
            changed["q"] = v

    return {"ok": True, "device_index": device_index, "changed": changed}


# ----- Compressor -----


def set_compressor(
    client: AbletonClient,
    track_index: int,
    *,
    threshold_db: float | None = None,
    ratio: float | None = None,
    attack_ms: float | None = None,
    release_ms: float | None = None,
    makeup_db: float | None = None,
) -> dict:
    """Adjust the first Compressor on the given track."""
    device_index = _find_device_by_class(client, track_index, COMPRESSOR_CLASS)
    if device_index is None:
        return {"ok": False, "reason": "no Compressor found on track"}

    names = client.get_device_parameter_names(track_index, device_index)
    changed: dict[str, float] = {}

    def maybe_set(param_name: str, value: float | None, lo: float, hi: float, key: str) -> None:
        if value is None:
            return
        idx = _find_param(names, param_name)
        if idx is None:
            return
        v = max(lo, min(hi, float(value)))
        client.set_device_parameter(track_index, device_index, idx, v)
        changed[key] = v

    maybe_set("Threshold", threshold_db, -60.0, 0.0, "threshold_db")
    maybe_set("Ratio", ratio, 1.0, 100.0, "ratio")
    maybe_set("Attack", attack_ms, 0.01, 300.0, "attack_ms")
    maybe_set("Release", release_ms, 1.0, 5000.0, "release_ms")
    maybe_set("Makeup", makeup_db, -36.0, 36.0, "makeup_db")

    return {"ok": True, "device_index": device_index, "changed": changed}


# ----- Sends -----


def set_send_to_return(
    client: AbletonClient,
    track_index: int,
    return_name: str,
    level: float,
) -> dict:
    """Set the send level from a track to a named return.

    `level` is a normalized 0.0-1.0 fader value.
    """
    return_index = find_return_index(client, return_name)
    if return_index is None:
        return {"ok": False, "reason": f"return '{return_name}' not found"}

    v = max(0.0, min(0.95, float(level)))
    client.set_track_send(track_index, return_index, v)
    return {
        "ok": True,
        "send_index": return_index,
        "level": v,
        "return_name": return_name,
    }


def get_send_to_return(
    client: AbletonClient, track_index: int, return_name: str
) -> float | None:
    return_index = find_return_index(client, return_name)
    if return_index is None:
        return None
    try:
        return client.get_track_send(track_index, return_index)
    except Exception:
        return None
