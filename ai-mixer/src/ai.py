"""Claude-powered mixing suggestions."""

import json
import os
from dataclasses import asdict

from anthropic import Anthropic

from analyzer import TrackFeatures

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are an expert mixing engineer. You are given:
- measured features of a REFERENCE track the user wants to match
- measured features of their CURRENT mix
- the list of track names in their Ableton Live session

Suggest concrete, conservative volume and pan adjustments that move the
current mix toward the reference. Only output adjustments for tracks that
exist in the provided track list. Use exact track names.

Volume changes must be small (between -3.0 and +3.0 dB).
Pan values are absolute targets between -1.0 (hard left) and 1.0 (hard right).

Respond as JSON only, no prose, with this exact shape:
{
  "suggestions": [
    {"track": "<name>", "param": "volume", "delta_db": <number>, "reason": "<short>"},
    {"track": "<name>", "param": "pan", "value": <number>, "reason": "<short>"}
  ]
}"""


def suggest_adjustments(
    reference: TrackFeatures,
    current: TrackFeatures,
    track_names: list[str],
) -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_msg = json.dumps(
        {
            "reference": asdict(reference),
            "current": asdict(current),
            "tracks": track_names,
        },
        indent=2,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)
