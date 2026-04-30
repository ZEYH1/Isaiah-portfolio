"""Streamlit UI for the AI mixing assistant."""

from dataclasses import asdict
from pathlib import Path

import streamlit as st

import device_map
from ableton_osc import AbletonClient, db_to_fader_delta
from ai import suggest_adjustments
from analyzer import analyze
from knowledge import list_guides


st.set_page_config(page_title="AI Mixing Assistant", layout="wide")
st.title("AI Mixing Assistant")


# ---------- Sidebar: Ableton connection ----------

st.sidebar.header("Ableton")
host = st.sidebar.text_input("Host", "127.0.0.1")
send_port = st.sidebar.number_input("Send port", value=11000, step=1)
recv_port = st.sidebar.number_input("Receive port", value=11001, step=1)

if st.sidebar.button("Connect / refresh tracks"):
    if "client" in st.session_state:
        st.session_state.client.close()
    try:
        client = AbletonClient(host, int(send_port), int(recv_port))
        names = client.get_track_names()
        try:
            return_names = client.get_return_track_names()
        except Exception:
            return_names = []
        st.session_state.client = client
        st.session_state.track_names = names
        st.session_state.return_names = return_names
        st.sidebar.success(
            f"Connected. {len(names)} tracks, {len(return_names)} returns."
        )
    except Exception as exc:
        st.sidebar.error(f"Connection failed: {exc}")

if "track_names" in st.session_state:
    st.sidebar.write("**Tracks:**")
    for i, name in enumerate(st.session_state.track_names):
        st.sidebar.write(f"{i}. {name}")

if "return_names" in st.session_state and st.session_state.return_names:
    st.sidebar.write("**Returns:**")
    for i, name in enumerate(st.session_state.return_names):
        st.sidebar.write(f"{chr(65+i)}. {name}")

st.sidebar.header("Style")
genre = st.sidebar.selectbox(
    "Target genre",
    ["Auto", "UK Garage", "Garage", "House", "Deep House", "Drill", "Trap"],
    help="Tells Claude which conventions from the loaded guides apply.",
)

guides = list_guides()
if guides:
    with st.sidebar.expander(f"Loaded mixing guides ({len(guides)})"):
        for g in guides:
            st.write(f"- {g}")
else:
    st.sidebar.info("No guides loaded. Drop .md files into ai-mixer/knowledge/.")


# ---------- Main: upload + analyze ----------

col_ref, col_cur = st.columns(2)

with col_ref:
    st.subheader("Reference track")
    ref_file = st.file_uploader(
        "Upload reference audio",
        type=["wav", "mp3", "aif", "aiff", "flac"],
        key="ref",
    )

with col_cur:
    st.subheader("Current mix")
    cur_file = st.file_uploader(
        "Upload current mix bounce",
        type=["wav", "mp3", "aif", "aiff", "flac"],
        key="cur",
    )


def _save_upload(uploaded, name: str) -> Path:
    target = Path("references") / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(uploaded.read())
    return target


can_analyze = ref_file and cur_file and "track_names" in st.session_state
if not can_analyze:
    st.info("Connect to Ableton (sidebar) and upload both audio files to begin.")

if can_analyze and st.button("Analyze and suggest"):
    ref_path = _save_upload(ref_file, f"ref_{ref_file.name}")
    cur_path = _save_upload(cur_file, f"cur_{cur_file.name}")

    with st.spinner("Analyzing audio..."):
        ref_features = analyze(str(ref_path))
        cur_features = analyze(str(cur_path))

    st.session_state.features = {
        "reference": asdict(ref_features),
        "current": asdict(cur_features),
    }

    with st.spinner("Asking Claude for suggestions..."):
        result = suggest_adjustments(
            ref_features,
            cur_features,
            st.session_state.track_names,
            return_names=st.session_state.get("return_names", []),
            genre=genre,
        )

    st.session_state.suggestions = result.get("suggestions", [])


# ---------- Results: features + suggestion checkboxes ----------

if "features" in st.session_state:
    with st.expander("Audio features (reference vs current)"):
        st.json(st.session_state.features)


# --- Safety guardrails ---
MAX_VOLUME_DELTA_DB = 2.0
FADER_UNITY = 0.85
PAN_CENTER_TRACKS = {"kick", "bass", "sub", "lead vocal", "vocal"}
PAN_CENTER_LIMIT = 0.1
EQ_GAIN_LIMIT_DB = 6.0
SEND_LEVEL_CEILING = 0.8


def _name_to_index(name: str) -> int | None:
    for i, n in enumerate(st.session_state.track_names):
        if n.strip().lower() == name.strip().lower():
            return i
    return None


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _sanitize(suggestion: dict) -> tuple[dict, list[str]]:
    s = dict(suggestion)
    notes: list[str] = []
    action = s.get("action") or s.get("param")
    s["action"] = action

    if action == "volume":
        delta = float(s.get("delta_db", 0))
        clamped = _clamp(delta, -MAX_VOLUME_DELTA_DB, MAX_VOLUME_DELTA_DB)
        if clamped != delta:
            notes.append(f"volume clamped {delta:+.1f} -> {clamped:+.1f} dB")
        s["delta_db"] = clamped

    elif action == "pan":
        v = float(s.get("value", 0))
        track_lower = str(s.get("track", "")).strip().lower()
        if track_lower in PAN_CENTER_TRACKS:
            limited = _clamp(v, -PAN_CENTER_LIMIT, PAN_CENTER_LIMIT)
            if limited != v:
                notes.append(f"low/center pan {v:+.2f} -> {limited:+.2f}")
            v = limited
        s["value"] = _clamp(v, -1.0, 1.0)

    elif action == "eq_band":
        if "gain_db" in s and s["gain_db"] is not None:
            g = float(s["gain_db"])
            clamped = _clamp(g, -EQ_GAIN_LIMIT_DB, EQ_GAIN_LIMIT_DB)
            if clamped != g:
                notes.append(f"EQ gain clamped {g:+.1f} -> {clamped:+.1f} dB")
            s["gain_db"] = clamped

    elif action == "send":
        lvl = float(s.get("level", 0))
        clamped = _clamp(lvl, 0.0, SEND_LEVEL_CEILING)
        if clamped != lvl:
            notes.append(f"send level capped {lvl:.2f} -> {clamped:.2f}")
        s["level"] = clamped

    return s, notes


def _label_for(s: dict) -> str:
    action = s.get("action")
    track = s.get("track", "?")
    reason = s.get("reason", "")
    if action == "volume":
        return f"**{track}** volume {s.get('delta_db', 0):+.1f} dB — {reason}"
    if action == "pan":
        return f"**{track}** pan to {s.get('value', 0):+.2f} — {reason}"
    if action == "eq_band":
        parts = [f"band {s.get('band', '?')}"]
        if s.get("freq_hz") is not None:
            parts.append(f"{s['freq_hz']:.0f} Hz")
        if s.get("gain_db") is not None:
            parts.append(f"{s['gain_db']:+.1f} dB")
        if s.get("q") is not None:
            parts.append(f"Q {s['q']:.1f}")
        return f"**{track}** EQ " + ", ".join(parts) + f" — {reason}"
    if action == "compressor":
        parts = []
        for k, label in [
            ("threshold_db", "thresh {:+.1f} dB"),
            ("ratio", "ratio {:.1f}"),
            ("attack_ms", "atk {:.1f} ms"),
            ("release_ms", "rel {:.0f} ms"),
            ("makeup_db", "makeup {:+.1f} dB"),
        ]:
            if s.get(k) is not None:
                parts.append(label.format(s[k]))
        return f"**{track}** Compressor " + ", ".join(parts) + f" — {reason}"
    if action == "send":
        return (
            f"**{track}** send to {s.get('to_return', '?')} = "
            f"{s.get('level', 0):.2f} — {reason}"
        )
    return f"**{track}** {action} — {reason}"


def _apply(client: AbletonClient, s: dict) -> tuple[bool, str]:
    """Apply a sanitized suggestion. Returns (ok, message)."""
    action = s.get("action")
    idx = _name_to_index(s.get("track", ""))
    if idx is None:
        return False, f"track '{s.get('track')}' not found"

    if action == "volume":
        cur = client.get_track_volume(idx)
        proposed = cur + db_to_fader_delta(float(s.get("delta_db", 0)))
        new = _clamp(proposed, 0.0, FADER_UNITY)
        client.set_track_volume(idx, new)
        return True, ""

    if action == "pan":
        client.set_track_panning(idx, float(s.get("value", 0)))
        return True, ""

    if action == "eq_band":
        result = device_map.set_eq_band(
            client,
            idx,
            int(s.get("band", 1)),
            freq_hz=s.get("freq_hz"),
            gain_db=s.get("gain_db"),
            q=s.get("q"),
        )
        return result.get("ok", False), result.get("reason", "")

    if action == "compressor":
        result = device_map.set_compressor(
            client,
            idx,
            threshold_db=s.get("threshold_db"),
            ratio=s.get("ratio"),
            attack_ms=s.get("attack_ms"),
            release_ms=s.get("release_ms"),
            makeup_db=s.get("makeup_db"),
        )
        return result.get("ok", False), result.get("reason", "")

    if action == "send":
        result = device_map.set_send_to_return(
            client,
            idx,
            str(s.get("to_return", "")),
            float(s.get("level", 0)),
        )
        return result.get("ok", False), result.get("reason", "")

    return False, f"unknown action '{action}'"


if st.session_state.get("suggestions"):
    st.subheader("Suggestions")

    sanitized: list[dict] = []
    notes: list[str] = []
    for raw in st.session_state.suggestions:
        clean, n = _sanitize(raw)
        sanitized.append(clean)
        for msg in n:
            notes.append(f"{clean.get('track', '?')}: {msg}")

    if notes:
        st.warning("Guardrails adjusted some suggestions:\n- " + "\n- ".join(notes))

    selections: list[bool] = []
    for i, s in enumerate(sanitized):
        selections.append(st.checkbox(_label_for(s), value=True, key=f"sug_{i}"))

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Snapshot current mixer state"):
            client = st.session_state.client
            snap = {"tracks": {}, "sends": {}}
            return_names = st.session_state.get("return_names", [])
            for i in range(len(st.session_state.track_names)):
                snap["tracks"][i] = {
                    "volume": client.get_track_volume(i),
                    "pan": client.get_track_panning(i),
                }
                snap["sends"][i] = {}
                for r_idx in range(len(return_names)):
                    try:
                        snap["sends"][i][r_idx] = client.get_track_send(i, r_idx)
                    except Exception:
                        pass
            st.session_state.snapshot = snap
            st.success("Snapshot saved (faders, pans, sends).")

    with col_b:
        if st.button("Apply selected"):
            client = st.session_state.client
            applied = 0
            failures: list[str] = []
            for s, on in zip(sanitized, selections):
                if not on:
                    continue
                ok, msg = _apply(client, s)
                if ok:
                    applied += 1
                else:
                    failures.append(f"{s.get('track', '?')}/{s.get('action')}: {msg}")
            st.success(f"Applied {applied} change(s).")
            if failures:
                st.warning("Some failed:\n- " + "\n- ".join(failures))

    with col_c:
        snap = st.session_state.get("snapshot")
        if st.button("Undo (restore snapshot)", disabled=snap is None):
            client = st.session_state.client
            for idx, vals in snap.get("tracks", {}).items():
                client.set_track_volume(idx, vals["volume"])
                client.set_track_panning(idx, vals["pan"])
            for idx, sends in snap.get("sends", {}).items():
                for r_idx, lvl in sends.items():
                    try:
                        client.set_track_send(idx, r_idx, lvl)
                    except Exception:
                        pass
            st.success("Restored faders, pans, and sends.")
