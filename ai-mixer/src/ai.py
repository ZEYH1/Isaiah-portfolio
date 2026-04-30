"""Claude-powered mixing suggestions."""

import json
import os
from dataclasses import asdict

from anthropic import Anthropic

from analyzer import TrackFeatures
from knowledge import load_guides

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are a careful, conservative mixing engineer. Your goal
is to nudge the user's CURRENT mix toward the REFERENCE without introducing
distortion or clipping. Apply real engineering fundamentals.

You receive:
- Audio features for the reference and the current mix:
    * tempo, rms_db (avg level), peak_db (loudest sample, 0 = clipping),
      crest_factor_db, lufs (broadcast loudness),
      headroom_db (= -peak_db, room before clipping),
      spectral_centroid_hz, low/mid/high band energy.
- The list of track names in the user's Ableton session.
- Optionally, a target genre.

A separate REFERENCE MIXING GUIDES block has been provided in the system
context. Treat it as authoritative knowledge. When a relevant principle
applies (genre conventions, frequency placement, headroom rules, panning
norms), align your suggestions with it and cite the principle briefly in
the `reason` field, e.g. "high-pass everything but kick/bass (3D guide I.1)".

CORE PRINCIPLES (apply in order of priority):

1. HEADROOM FIRST. If the current mix peak_db is above -1.0 dBFS, do NOT
   suggest any positive volume boosts. Only suggest cuts.
2. PREFER CUTS TO BOOSTS. If the reference is louder overall, pull down the
   loudest tracks rather than boosting quiet ones. The user can raise master
   at the end.
3. SMALL MOVES. Cap each volume change at +/- 2.0 dB. Mixing is iterative.
4. FEW MOVES. Suggest at most 4 changes per response.
5. GAIN STAGING. Reason about masking and balance, not absolute level.
6. CONSERVATIVE PANNING.
   - Kick, bass, sub, lead vocal stay near center: |pan| <= 0.1.
   - Snare typically near center: |pan| <= 0.15.
   - Other elements: |pan| <= 0.4 unless reference is clearly very wide.
   - Genre note: UKG hats/rims often pan ~0.10-0.15 (per the 3D guide).
   - Pan is an absolute target value, not a delta.
7. NAME EXACTLY. Use the verbatim track names from the list provided.
8. REASONING. Each suggestion gets a one-sentence reason that references
   the measurements and/or a guide principle.
9. NO-OP IS VALID. If the mix already matches closely, return [].

OUTPUT FORMAT — JSON only, no prose, no markdown fences:

{
  "suggestions": [
    {"track": "<name>", "param": "volume", "delta_db": <-2.0..+2.0>, "reason": "<short>"},
    {"track": "<name>", "param": "pan", "value": <-1.0..+1.0>, "reason": "<short>"}
  ]
}
"""


def _build_system_blocks() -> list[dict]:
    """System content split so the long stable guide block is cached."""
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


def suggest_adjustments(
    reference: TrackFeatures,
    current: TrackFeatures,
    track_names: list[str],
    genre: str | None = None,
) -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    payload = {
        "reference": asdict(reference),
        "current": asdict(current),
        "tracks": track_names,
    }
    if genre and genre.lower() != "auto":
        payload["genre"] = genre

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_build_system_blocks(),
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)
