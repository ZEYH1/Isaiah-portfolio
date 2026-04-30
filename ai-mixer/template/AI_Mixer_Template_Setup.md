# AI Mixer — Live Template Setup

A one-time setup. Once saved as your default set, every new project you start
will already have the return tracks and devices the AI Mixer expects. The
assistant talks to plugins through these returns, so the names below must
match exactly.

---

## Step 1 — Open Ableton with an empty Set

`File → New Live Set`. Don't load any existing template yet.

## Step 2 — Add five return tracks

A return track lives at the bottom of the Session view. By default Ableton
gives you two returns ("A Reverb" and "B Delay"). You'll rename those and
add three more.

1. **Rename Return A** to `Parallel Comp` (double-click the title).
2. **Rename Return B** to `Plate Reverb`.
3. Add three more returns: `Create → Insert Return Track` (Cmd+Alt+T / Win+Alt+T) three times.
4. Rename the new ones in order: `Hall Reverb`, `1/8 Slap`, `1/4 Dotted`.

You should now have these five returns, in this order:

| Letter | Name | Purpose |
|---|---|---|
| A | Parallel Comp | Heavy compressor for drums |
| B | Plate Reverb | Short space for vocals/snares |
| C | Hall Reverb | Long space for pads/atmosphere |
| D | 1/8 Slap | Vocal slap delay (Trap, UKG) |
| E | 1/4 Dotted | Rhythmic delay for throws/transitions |

> The names matter — the AI assistant looks them up by name. If you spell
> them differently, edit `ai-mixer/src/device_map.py` to match.

## Step 3 — Load and configure the device on each return

For each return, drag the device from Ableton's browser onto that return
track and dial in the starting settings below. These are sensible defaults;
you'll tune them to taste later.

### Return A — Parallel Comp

Device: **Audio Effects → Dynamics → Compressor**

| Parameter | Value |
|---|---|
| Threshold | -28 dB |
| Ratio | 8:1 |
| Attack | 1.0 ms |
| Release | 60 ms |
| Knee | 6 dB |
| Makeup | +8 dB |
| Dry/Wet | 100% |

Heavy compression that you blend in via send level on drum tracks.

### Return B — Plate Reverb

Device: **Audio Effects → Reverb**

| Parameter | Value |
|---|---|
| Decay Time | 1.4 s |
| Predelay | 25 ms |
| Size | 70 |
| Diffusion | 80% |
| Dry/Wet | 100% |
| In Filter (HP) | 250 Hz |
| In Filter (LP) | 8000 Hz |

Short, controlled space. Use this for vocals and snares.

### Return C — Hall Reverb

Device: **Audio Effects → Reverb**

| Parameter | Value |
|---|---|
| Decay Time | 3.5 s |
| Predelay | 30 ms |
| Size | 120 |
| Diffusion | 85% |
| Dry/Wet | 100% |
| In Filter (HP) | 200 Hz |
| In Filter (LP) | 6000 Hz |

Longer space for pads and atmospheric depth. Send sparingly.

### Return D — 1/8 Slap

Device: **Audio Effects → Echo**

| Parameter | Value |
|---|---|
| Sync | On |
| L Sync Mode | Notes |
| L 16th | 8th note (L Time = 1/8) |
| Mirror Time L→R | On |
| Feedback | 15% |
| Dry/Wet | 100% |
| Filter HP | 250 Hz |
| Filter LP | 7000 Hz |

Tight slap delay, mostly for vocals.

### Return E — 1/4 Dotted

Device: **Audio Effects → Echo**

| Parameter | Value |
|---|---|
| Sync | On |
| L Sync Mode | Notes |
| L 16th | Dotted 1/4 |
| Mirror Time L→R | On |
| Feedback | 30% |
| Dry/Wet | 100% |

Rhythmic dub-style delay for throws and transitions.

## Step 4 — Sends from every track default to ZERO

Click on a regular track and look at the colored send knobs (A B C D E).
Make sure they're all at the bottom (-inf). The assistant will raise
specific sends; if your starting state has random sends already up, the
suggestions will sound wrong.

## Step 5 — Save as the default Set

1. `File → Save Live Set As…`
2. Save it somewhere clear like `~/Music/Ableton Templates/AI_Mixer.als`.
3. Then: `Live → Settings → File / Folder` (or `Preferences`).
4. Find **Default Live Set** at the bottom.
5. Click `Set` and choose the file you just saved.

From now on, every new Live Set you create starts from this template, and
the AI Mixer will recognize all five returns the moment you connect.

---

## Verifying it works

After saving, open a fresh Live Set (`Cmd+N`) and:

1. Confirm you see five returns named exactly `Parallel Comp`, `Plate Reverb`,
   `Hall Reverb`, `1/8 Slap`, `1/4 Dotted`.
2. In the AI Mixer Streamlit app, click `Connect / refresh tracks` — you
   should see the returns show up alongside your regular tracks.
3. Run a test from Terminal:

   ```bash
   python -c "from src.ableton_osc import AbletonClient; c = AbletonClient(); print(c.get_return_tracks())"
   ```

   You should see all five return names printed.
