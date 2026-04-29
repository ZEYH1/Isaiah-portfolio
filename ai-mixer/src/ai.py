"""Claude-powered mixing suggestions."""

import json
import os
from dataclasses import asdict

from anthropic import Anthropic

from .analyzer import TrackFeatures

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are an expert mixing engineer. Given measured features of a
reference track and a user's current mix, suggest concrete adjustments
(track volumes in dB, pan positions, EQ moves, compression). Respond as JSON
with shape: {"suggestions": [{"target": str, "action": str, "value": number,
"reason": str}]}."""


def suggest_adjustments(reference: TrackFeatures, current: TrackFeatures) -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_msg = json.dumps(
        {"reference": asdict(reference), "current": asdict(current)}, indent=2
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text
    return json.loads(text)
