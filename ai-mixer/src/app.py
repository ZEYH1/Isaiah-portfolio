"""Streamlit UI for the AI mixing assistant."""

from dataclasses import asdict
from pathlib import Path

import streamlit as st

from ableton_osc import AbletonClient, db_to_fader_delta
from ai import suggest_adjustments
from analyzer import analyze


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
        st.session_state.client = client
        st.session_state.track_names = names
        st.sidebar.success(f"Connected. {len(names)} tracks.")
    except Exception as exc:
        st.sidebar.error(f"Connection failed: {exc}")

if "track_names" in st.session_state:
    st.sidebar.write("**Tracks in session:**")
    for i, name in enumerate(st.session_state.track_names):
        st.sidebar.write(f"{i}. {name}")


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
            ref_features, cur_features, st.session_state.track_names
        )

    st.session_state.suggestions = result.get("suggestions", [])


# ---------- Results: features + suggestion checkboxes ----------

if "features" in st.session_state:
    with st.expander("Audio features (reference vs current)"):
        st.json(st.session_state.features)


# --- Safety guardrails: never trust the LLM to respect numeric limits ---
MAX_VOLUME_DELTA_DB = 2.0     # cap per-suggestion volume move
FADER_UNITY = 0.85            # AbletonOSC linear value for 0 dB
FADER_CEILING = FADER_UNITY   # never push a fader past unity gain
PAN_CENTER_TRACKS = {"kick", "bass", "sub", "lead vocal", "vocal"}
PAN_CENTER_LIMIT = 0.1


def _name_to_index(name: str) -> int | None:
    for i, n in enumerate(st.session_state.track_names):
        if n.strip().lower() == name.strip().lower():
            return i
    return None


def _sanitize(suggestion: dict) -> tuple[dict, str | None]:
    """Clamp a Claude suggestion to safe ranges. Returns (clean, note)."""
    s = dict(suggestion)
    note = None
    if s.get("param") == "volume":
        delta = float(s.get("delta_db", 0))
        clamped = max(-MAX_VOLUME_DELTA_DB, min(MAX_VOLUME_DELTA_DB, delta))
        if clamped != delta:
            note = f"clamped {delta:+.1f} -> {clamped:+.1f} dB"
        s["delta_db"] = clamped
    elif s.get("param") == "pan":
        v = float(s.get("value", 0))
        track_lower = str(s.get("track", "")).strip().lower()
        if track_lower in PAN_CENTER_TRACKS:
            limited = max(-PAN_CENTER_LIMIT, min(PAN_CENTER_LIMIT, v))
            if limited != v:
                note = f"low/center element pan {v:+.2f} -> {limited:+.2f}"
            v = limited
        v = max(-1.0, min(1.0, v))
        s["value"] = v
    return s, note


if st.session_state.get("suggestions"):
    st.subheader("Suggestions")

    sanitized: list[dict] = []
    notes: list[str] = []
    for raw in st.session_state.suggestions:
        clean, note = _sanitize(raw)
        sanitized.append(clean)
        if note:
            notes.append(f"{clean.get('track', '?')}: {note}")

    if notes:
        st.warning("Guardrails adjusted some suggestions:\n- " + "\n- ".join(notes))

    selections: list[bool] = []
    for i, s in enumerate(sanitized):
        track = s.get("track", "?")
        param = s.get("param", "?")
        if param == "volume":
            label = f"**{track}** volume {s.get('delta_db', 0):+.1f} dB — {s.get('reason', '')}"
        else:
            label = f"**{track}** pan to {s.get('value', 0):+.2f} — {s.get('reason', '')}"
        selections.append(st.checkbox(label, value=True, key=f"sug_{i}"))

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Snapshot current mixer state"):
            client = st.session_state.client
            snap = {}
            for i in range(len(st.session_state.track_names)):
                snap[i] = {
                    "volume": client.get_track_volume(i),
                    "pan": client.get_track_panning(i),
                }
            st.session_state.snapshot = snap
            st.success("Snapshot saved.")

    with col_b:
        if st.button("Apply selected"):
            client = st.session_state.client
            applied, skipped, capped = 0, [], []
            for s, on in zip(sanitized, selections):
                if not on:
                    continue
                idx = _name_to_index(s.get("track", ""))
                if idx is None:
                    skipped.append(f"{s.get('track')} (no matching track)")
                    continue
                if s.get("param") == "volume":
                    cur = client.get_track_volume(idx)
                    proposed = cur + db_to_fader_delta(float(s.get("delta_db", 0)))
                    new = max(0.0, min(FADER_CEILING, proposed))
                    if new != proposed:
                        capped.append(f"{s.get('track')} fader capped at unity")
                    client.set_track_volume(idx, new)
                    applied += 1
                elif s.get("param") == "pan":
                    client.set_track_panning(idx, float(s.get("value", 0)))
                    applied += 1
            st.success(f"Applied {applied} change(s).")
            if capped:
                st.warning("Headroom guardrail: " + "; ".join(capped))
            if skipped:
                st.warning("Skipped: " + ", ".join(skipped))

    with col_c:
        snap = st.session_state.get("snapshot")
        if st.button("Undo (restore snapshot)", disabled=snap is None):
            client = st.session_state.client
            for idx, vals in snap.items():
                client.set_track_volume(idx, vals["volume"])
                client.set_track_panning(idx, vals["pan"])
            st.success("Restored.")
