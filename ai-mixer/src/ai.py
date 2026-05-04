"""Claude-powered mixing suggestions.

Action types Claude can output:
  volume       - track fader delta
  pan          - track pan position
  eq_band      - EQ Eight band (Ableton native)
  compressor   - Compressor parameters (Ableton native)
  send         - send level to a named return track
  sidechain    - configure sidechain compression (kick -> bass / pads)
  transient    - transient shaper attack/sustain control
  slate_param  - third-party Slate Digital plugin parameter (Phase 2 mapping)
"""

import json
import os
from dataclasses import asdict

from anthropic import Anthropic

from analyzer import TrackFeatures
from knowledge import load_guides

MODEL = "claude-opus-4-7"

# ---- Guardrails (server-side enforcement on Claude's output) ---------------
GUARDRAILS = {
    "eq_gain_max_db": 6.0,
    "volume_delta_max_db": 2.0,
    "send_max": 0.8,
    "fader_max": 0.85,                          # ~ unity (0 dBFS)
    "sidechain_ratio_max": 10.0,
    "sidechain_threshold_min": -40.0,
    "transient_attack_range": (-12.0, 12.0),    # dB relative
    "transient_sustain_range": (-12.0, 12.0),
}

SYSTEM_PROMPT = """You are a careful, conservative mixing engineer. Your goal
is to nudge the user's CURRENT mix toward the REFERENCE without introducing
distortion or clipping. Apply real engineering fundamentals.

You receive:
- Audio features for the reference and the current mix.
- The list of track names in the user's Ableton session.
- The list of return tracks (the user has set up a standard template with
  return tracks named: Parallel Comp, Plate Reverb, Hall Reverb, 1/8 Slap,
  1/4 Dotted -- each with the appropriate device pre-loaded).
- Optionally, a target genre.
- Optionally, the session tempo (use it to tune sidechain release timing).
- Optionally, a list of Slate Digital plugins that have been mapped on tracks.

A separate REFERENCE MIXING GUIDES block has been provided in the system
context. Treat it as authoritative knowledge. When a relevant principle
applies, cite it briefly in the `reason` field.

CORE PRINCIPLES (apply in order of priority):

1. HEADROOM FIRST. If the current peak_db > -1.0 dBFS, do NOT suggest any
   positive volume boosts -- only cuts.
2. PREFER CUTS TO BOOSTS, both for fader moves and EQ.
3. SMALL MOVES. Cap each move at the limits given per action type below.
4. FEW MOVES. Maximum 6 changes per response across all action types.
5. CONSERVATIVE PANNING.
   - Kick, bass, sub, lead vocal: |pan| <= 0.1.
   - Snare: |pan| <= 0.15.
   - Other elements: |pan| <= 0.4 unless reference is clearly very wide.
6. NAME EXACTLY. Use verbatim track names from the provided list.
7. REASON CONCISELY. Each action gets a one-sentence reason citing a
   measurement and/or a guide principle.
8. NO-OP IS VALID. Empty list if nothing should change.

ACTION TYPES (output any combination):

a) Volume
   {"action": "volume", "track": "<name>", "delta_db": <-2.0..+2.0>, "reason": "..."}

b) Pan
   {"action": "pan", "track": "<name>", "value": <-1.0..+1.0>, "reason": "..."}

c) EQ band -- adjusts an Ableton EQ Eight on the track. Bands are 1-8.
   Typical band placements: 1=high-pass/low cut, 2=low shelf, 3-6=parametric,
   7=high shelf, 8=low-pass/high cut.
   {
     "action": "eq_band",
     "track": "<name>",
     "band": <1..8>,
     "freq_hz": <20..22000>,    // optional
     "gain_db": <-6.0..+6.0>,   // optional
     "q": <0.3..3.0>,           // optional
     "reason": "..."
   }

d) Compressor -- adjusts an Ableton Compressor on the track. Only include
   parameters you actually want to change.
   {
     "action": "compressor",
     "track": "<name>",
     "threshold_db": <-30..0>,    // optional
     "ratio": <1.5..8.0>,         // optional
     "attack_ms": <0.1..50>,      // optional
     "release_ms": <20..400>,     // optional
     "makeup_db": <-3..6>,        // optional
     "reason": "..."
   }

e) Send to a return track -- this is how you add parallel comp, reverb,
   delay. `level` is the send fader 0.0-0.8.
   Valid `to_return` values:
     - "Parallel Comp"  (heavy comp, blend in for drum body)
     - "Plate Reverb"   (short space for vocals/snares)
     - "Hall Reverb"    (long space for pads)
     - "1/8 Slap"       (vocal slap delay)
     - "1/4 Dotted"     (rhythmic delay throws)
   {
     "action": "send",
     "track": "<name>",
     "to_return": "<one of above>",
     "level": <0.0..0.8>,
     "reason": "..."
   }

f) Sidechain -- configure kick-to-bass (or kick-to-pads) sidechain compression.
   The target track must have an Ableton Compressor; if not, the host will
   surface manual setup steps. Use this for tech house, future house, and
   UK garage when bass crest factor is low (< 8 dB) or genre clearly demands it.
   {
     "action": "sidechain",
     "trigger_track": "<track that triggers the duck, e.g. Kick>",
     "target_track":  "<track being ducked, e.g. Bass>",
     "threshold_db":  <-40..0>,
     "ratio":         <1.5..10.0>,
     "attack_ms":     <0.1..20>,    // 0.1-5 for tight pumping; up to 20 for pads
     "release_ms":    <10..800>,    // tune to the BPM (1 beat at 127 BPM = 472 ms)
     "depth_db":      <2.0..8.0>,   // how much GR to aim for
     "reason": "..."
   }

g) Transient -- shape attack/sustain via Ableton's Transient Shaper.
   {
     "action": "transient",
     "track": "<name>",
     "attack_delta_db":  <-12..+12>,  // - softens, + adds snap
     "sustain_delta_db": <-12..+12>,  // - tightens body, + lengthens
     "reason": "..."
   }
   Use on: kick (sustain -2 to -6 to tighten), snare (attack +2 to +4 for
   crack), bass (sustain -2 to -4 to reduce smearing).

h) Slate plugin parameter -- ONLY if the plugin appears in the loaded plugin
   maps provided in the user message. Do not guess parameter names.
   {
     "action": "slate_param",
     "track": "<name>",
     "plugin": "<FG-Dynamics | Infinity EQ | FG-X2 | VBC | Fresh Air | Verbsuite | Submerge>",
     "parameter": "<exact parameter name from the provided mapping>",
     "value": <float>,
     "reason": "..."
   }

GUIDANCE PER ACTION:
- Use EQ surgically. Cuts in the 200-500 Hz region for mud, gentle high-shelf
  cuts for warmth, a small high-shelf boost (~+1 dB at 12 kHz) for "air" on
  vocals/tops only.
- Use compressor moves to glue, not to crush. Typical drum-bus or vocal
  compressor: ratio 2.5-4, attack 5-15 ms, release 80-150 ms, threshold
  set for 2-4 dB GR.
- Parallel comp send: typical level 0.3-0.5 for drums; never above 0.6.
- Reverb send: vocals 0.15-0.3 to Plate; pads 0.2-0.4 to Hall. Avoid sending
  kick/bass/sub to any reverb.
- Delay send: vocals 0.15-0.3 to 1/8 Slap. Use 1/4 Dotted only for specific
  throws/transitions.
- Sidechain: ALWAYS suggest kick->bass for tech house / future house / UK
  garage if bass crest factor is low and no sidechain is present yet.
  Tune release_ms rhythmically to the BPM provided.
- Transient: prefer over EQ for changing perceived punch on drums and bass.
- slate_param: only when the plugin name appears in the loaded plugin maps.

OUTPUT FORMAT -- JSON only, no prose, no markdown fences:

{
  "suggestions": [
    { ...action object as above... },
    ...
  ]
}
"""


def _build_system_blocks() -> list[dict]:
    blocks: list[dict] = [{"type": "text", "text": SYSTEM_PROMPT}]
    guides = load_guides()
    if guides:
        blocks.append(
            {
                "type": "text",
                "text": "REFERENCE MIXING GUIDES:\n\n" + guides,
                "cache_control": {"type": "ephemeral"},
            }
        )
    return blocks


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _apply_guardrails(s: dict) -> dict | None:
    """Clamp Claude's output to safe ranges. Mutates and returns s; returns
    None to drop the suggestion entirely. Field names match the schema in
    SYSTEM_PROMPT (and the consumer-side _sanitize in app.py)."""
    action = s.get("action")

    if action == "volume":
        s["delta_db"] = _clamp(
            float(s.get("delta_db", 0)),
            -GUARDRAILS["volume_delta_max_db"],
            GUARDRAILS["volume_delta_max_db"],
        )

    elif action == "pan":
        v = float(s.get("value", 0))
        s["value"] = _clamp(v, -1.0, 1.0)

    elif action == "eq_band":
        if s.get("gain_db") is not None:
            s["gain_db"] = _clamp(
                float(s["gain_db"]),
                -GUARDRAILS["eq_gain_max_db"],
                GUARDRAILS["eq_gain_max_db"],
            )

    elif action == "send":
        s["level"] = _clamp(float(s.get("level", 0)), 0.0, GUARDRAILS["send_max"])

    elif action == "compressor":
        if s.get("ratio") is not None:
            s["ratio"] = _clamp(float(s["ratio"]), 1.0, 8.0)
        if s.get("attack_ms") is not None:
            s["attack_ms"] = _clamp(float(s["attack_ms"]), 0.1, 50.0)
        if s.get("release_ms") is not None:
            s["release_ms"] = _clamp(float(s["release_ms"]), 20.0, 400.0)

    elif action == "sidechain":
        s["ratio"] = _clamp(
            float(s.get("ratio", 4.0)), 1.0, GUARDRAILS["sidechain_ratio_max"]
        )
        s["threshold_db"] = max(
            GUARDRAILS["sidechain_threshold_min"], float(s.get("threshold_db", -20.0))
        )
        s["depth_db"] = _clamp(float(s.get("depth_db", 3.0)), 1.0, 8.0)
        s["attack_ms"] = _clamp(float(s.get("attack_ms", 1.0)), 0.1, 50.0)
        s["release_ms"] = _clamp(float(s.get("release_ms", 150.0)), 10.0, 800.0)

    elif action == "transient":
        lo, hi = GUARDRAILS["transient_attack_range"]
        s["attack_delta_db"] = _clamp(float(s.get("attack_delta_db", 0)), lo, hi)
        lo, hi = GUARDRAILS["transient_sustain_range"]
        s["sustain_delta_db"] = _clamp(float(s.get("sustain_delta_db", 0)), lo, hi)

    elif action == "slate_param":
        # Pass through; range validation happens in the per-plugin device map.
        pass

    return s


def suggest_adjustments(
    reference: TrackFeatures,
    current: TrackFeatures,
    track_names: list[str],
    return_names: list[str] | None = None,
    genre: str | None = None,
    tempo_bpm: float | None = None,
    device_maps: dict | None = None,
) -> dict:
    """Ask Claude for mixing suggestions and return {"suggestions": [...]}.

    tempo_bpm and device_maps are optional context that, when provided,
    enable BPM-aware sidechain timing and Slate plugin parameter suggestions.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    payload: dict = {
        "reference": asdict(reference),
        "current": asdict(current),
        "tracks": track_names,
        "return_tracks": return_names or [],
    }
    if genre and genre.lower() != "auto":
        payload["genre"] = genre

    if tempo_bpm:
        beat_ms = round(60000.0 / float(tempo_bpm), 1)
        payload["tempo_bpm"] = tempo_bpm
        payload["tempo_hint"] = (
            f"Session tempo: {tempo_bpm} BPM "
            f"(1 beat = {beat_ms} ms, half beat = {round(beat_ms / 2, 1)} ms). "
            f"Use this to tune sidechain release_ms."
        )

    if device_maps:
        payload["loaded_plugin_maps"] = device_maps

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_build_system_blocks(),
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    parsed = json.loads(text)

    # Apply server-side guardrails to each suggestion
    raw_suggestions = parsed.get("suggestions", [])
    cleaned = [r for r in (_apply_guardrails(s) for s in raw_suggestions) if r]
    parsed["suggestions"] = cleaned
    return parsed
