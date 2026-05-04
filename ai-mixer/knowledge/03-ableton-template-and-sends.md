# The AI Mixer Live Template and How to Use Sends

The user has set up a standardized Ableton template with five named return
tracks. The assistant should use **sends** to apply parallel compression,
reverb, and delay rather than trying to insert plugins on individual tracks.

## Available returns and what they do

| Return | Device | Purpose | Typical send level |
|---|---|---|---|
| Parallel Comp | Compressor (8:1, -28 dB thresh, 1ms/60ms, +8 dB makeup) | Heavy parallel compression — adds body and density to drums without crushing transients. | Drums: 0.30-0.50. Never above 0.60. |
| Plate Reverb | Reverb (1.4 s decay, 25 ms predelay, HP 250 Hz) | Short, controlled space. Vocals and snares. | Vocals: 0.15-0.30. Snares: 0.10-0.20. |
| Hall Reverb | Reverb (3.5 s decay, 30 ms predelay, HP 200 Hz) | Long atmospheric space. Pads, ambient elements. | Pads: 0.20-0.40. Use sparingly. |
| 1/8 Slap | Echo (1/8 sync, 15% feedback) | Short tight slap delay. | Vocals: 0.15-0.30. |
| 1/4 Dotted | Echo (dotted 1/4 sync, 30% feedback) | Rhythmic dub-style delay for throws and transitions. | Vocals/leads: 0.10-0.20, only on specific moments. |

## Send rules the assistant must follow

1. **Never send kick, sub, or bass to any reverb or delay return.** Low-end
   reverberation muddies the mix and kills club translation. Reverb on bass
   is a beginner mistake.
2. **Parallel comp is for drums and drum bus only**, not vocals or melody.
   For vocals, use insert compression or a separate vocal-comp return if the
   user has one.
3. **Plate over Hall by default.** Plate reverb sits forward and articulate.
   Hall is for explicit "huge space" moments only.
4. **Slap delay before reverb when adding vocal depth.** Slap delay creates
   the sense of distance much more efficiently than reverb wash.
5. **Send levels accumulate.** If a track already has a 0.30 plate send,
   don't suggest another 0.30 — suggest a delta or a target level that
   takes the existing send into account.

## Per-genre default send philosophy

### UK Garage (Sammy Virji, Notion lineage)
- Vocal chops: 1/8 Slap at 0.20-0.25, Plate at 0.10-0.15.
- Snares: Plate at 0.10-0.15. Keep dry and forward.
- Top loops: light Hall send (0.10-0.15) for air, never more.
- No parallel comp on individual percussion; parallel comp on the **drum
  bus** if available.

### Deep House (Avaion lineage)
- Top loops: Plate at 0.15-0.20 + Hall at 0.10-0.15. Stack two reverbs at
  small amounts for depth.
- Vocal: 1/4 Dotted at 0.10-0.15 for emotional throws on key phrases.
- Pads: Hall at 0.30-0.40, embraced as the genre's signature space.

### Drill (UK)
- Snares: dry. At most 0.10 to Plate. Long reverb on the halftime snare
  destroys impact.
- Vocals: 1/8 Slap at 0.15. Plate at 0.10. Avoid Hall entirely on lead
  vocal — drill vocals are upfront and aggressive.
- 808s: dry. No sends.

### Trap
- Vocals: 1/8 Slap at 0.20-0.25. Plate at 0.10-0.15. Travis-style dry-and-
  upfront with depth from slap, not hall.
- Snares: Plate at 0.10-0.15. Optional 1/8 Slap at 0.05-0.10 for character.
- 808s: dry. No sends.

## Using EQ moves alongside sends

Reverb and delay sound better when the source is EQ'd appropriately first:

- **Before** sending a vocal to Plate: cut 200-300 Hz on the vocal (or use
  the return's input HP). Mud lives there.
- **Before** sending top loops to Hall: high-pass the top loop above 200 Hz
  so only the highs swim in the reverb.
- **Before** sending drums to Parallel Comp: the parallel comp does its own
  EQ via the return's chain (consider adding a subtle high-shelf cut on the
  return to keep the parallel signal warm).

The assistant should consider EQ + send as a coordinated pair: shape the
source first, then place it in space.
