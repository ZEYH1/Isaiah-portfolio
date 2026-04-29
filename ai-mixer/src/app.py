"""Streamlit UI for the AI mixing assistant."""

from dataclasses import asdict
from pathlib import Path

import streamlit as st

from analyzer import analyze
from ableton_osc import AbletonClient
from ai import suggest_adjustments


st.set_page_config(page_title="AI Mixing Assistant", layout="wide")
st.title("AI Mixing Assistant")

st.sidebar.header("Ableton connection")
host = st.sidebar.text_input("Host", "127.0.0.1")
port = st.sidebar.number_input("Send port", value=11000, step=1)

col_ref, col_cur = st.columns(2)

with col_ref:
    st.subheader("Reference track")
    ref_file = st.file_uploader("Upload reference audio", type=["wav", "mp3", "aif", "aiff", "flac"], key="ref")

with col_cur:
    st.subheader("Current mix")
    cur_file = st.file_uploader("Upload current mix bounce", type=["wav", "mp3", "aif", "aiff", "flac"], key="cur")


def _save_upload(uploaded, name: str) -> Path:
    target = Path("references") / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(uploaded.read())
    return target


if ref_file and cur_file and st.button("Analyze and suggest"):
    ref_path = _save_upload(ref_file, f"ref_{ref_file.name}")
    cur_path = _save_upload(cur_file, f"cur_{cur_file.name}")

    with st.spinner("Analyzing audio..."):
        ref_features = analyze(str(ref_path))
        cur_features = analyze(str(cur_path))

    st.json({"reference": asdict(ref_features), "current": asdict(cur_features)})

    with st.spinner("Asking Claude for suggestions..."):
        result = suggest_adjustments(ref_features, cur_features)

    st.subheader("Suggestions")
    st.json(result)

    if st.button("Apply to Ableton"):
        AbletonClient(host, int(port))
        st.info("Wire up suggestion -> OSC mapping in src/ableton_osc.py to apply.")
