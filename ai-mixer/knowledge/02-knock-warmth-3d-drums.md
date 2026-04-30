# Drum Texture: Knock, Warmth, Depth, and 3D Top Loops

This guide is about making drums feel **physical** rather than programmed —
the difference between a beat that "smacks" and one that just "plays."
Applies across all four target genres but is especially load-bearing for
**UK Garage** (Sammy Virji, Notion) and **House/Deep House** (Avaion).

---

## I. The three qualities, defined

| Quality | What you're going for | What it sounds like missing |
|---|---|---|
| **Knock** | Tight, focused low-mid impact on kick and snare. The "thump in the chest" feel. | Boomy and undefined, or thin and clicky with no body. |
| **Warmth** | Harmonic richness, gentle saturation, slightly rolled-off highs. Drums sound like they live in a room, not a void. | Sterile, brittle, "in-the-box," fatiguing. |
| **Depth (3D)** | Drums occupy distinct positions in width, height, and front/back. The kit feels three-dimensional, not pasted onto a flat plane. | Flat, mono-feeling, everything stacked at the same distance. |

---

## II. Knock — getting the punch

### The layering formula
Stack three layers per drum hit, each occupying a different frequency zone:

| Layer | Kick example | Snare example | Frequency role |
|---|---|---|---|
| **Body** | 808-style sub kick | Body snare sample | 60-250 Hz — the weight |
| **Click / Crack** | 909 transient layer | Clap layer | 2-5 kHz — the attack |
| **Air** (optional) | High noise tail | Top noise/breath | 8-12 kHz — the presence |

**Rules:**
- High-pass everything but the body layer at ~120 Hz. Multiple things in the
  sub region = mud and phase issues.
- **Always check phase between layers.** Two snares that both trigger at
  sample 0 will often hollow each other out — nudge one a few samples or
  flip polarity. (Sample Focus, *6 Snare Processing Techniques*)
- The click layer is the loudest by perceived attack; the body is the loudest
  by RMS; the air layer is the quietest but glues the others together.

### Parallel compression for body without sacrifice
Send the drum bus to a **parallel** compressor channel:
- Ratio 10:1, fast attack, medium release, hammering 8-15 dB GR
- Blend the parallel channel **under** the dry drums until you hear the
  drums "thicken" without the transient softening. Typically -8 to -12 dB
  under the dry. (Mystic Alankar, *Drum Layering in Hip-Hop*)
- This adds power without losing dynamics — the dry transient is preserved,
  the parallel adds sustained body and density.

### Transient design
- Use a transient shaper (SPL Transient Designer, FabFilter Pro-Q in dynamic
  mode) to **add** attack to soft samples, or **soften** an over-clicky
  kick. 1-2 dB of attack boost is usually plenty.
- For UK Garage and Drill, lean toward **softening** the snare attack
  slightly — a sharp snap reads as trap; a rounder, woodier snare reads
  as garage/drill.

---

## III. Warmth — making drums sound like they live in a room

### Saturation, in three intensities

| Intensity | Plugin examples | What it does | Where it goes |
|---|---|---|---|
| **Hair / sheen** | iZotope Vintage Tape, Softube Tape, UAD Studer | Subtle harmonics, gentle high-end roll | Drum bus, master |
| **Color / glue** | Soundtoys Decapitator (Tube setting, Drive 3-5), FabFilter Saturn (Tape) | Adds harmonic density and warmth without obvious distortion | Drum bus, individual snare/clap layers |
| **Grit / character** | Decapitator (Punish), Trash, Soft clipper | Audible saturation and edge | Top loops, breaks, lo-fi snares |

**Rules:**
- Saturate **before** EQ in the chain when you want harmonic-driven brightness;
  **after** EQ when you want clean tone-shaping then warmth.
- Apply parallel saturation if you don't want the dry transients touched —
  send to a 100% wet saturated bus and blend.
- Too much saturation muddies the low end. If the kick sub starts losing
  pitch clarity, you've gone too far.

### The "tape glue" master move
On the drum bus, in this order:
1. Light bus comp: ~1.5-2 dB GR, slow attack (~30 ms), auto release. Glue,
   not crush.
2. Tape saturation: just enough that bypassing it sounds slightly thinner
   and brighter.
3. Optional: gentle low-shelf cut at ~80 Hz on the bus (-1 dB) to undo any
   sub buildup the saturation added.

This is the engineer's "warmth knob." It's how Sammy Virji's bouncy
Virji-style drums hold together when you have a chopped break, programmed
kick, and shaker all stacked.

### Frequency moves for warmth (not just saturation)
- **Cut, don't boost** to create warmth. A subtle cut around 4-6 kHz often
  reads as warmer than a low-mid boost.
- **Gentle low-mid boost (200-400 Hz, ~+1.5 dB)** on the kick adds weight
  without muddying.
- **High-shelf cut at 12 kHz (~-1 dB)** on a too-bright loop instantly
  reads as analog warmth.

---

## IV. Depth (3D) — width, height, front/back

### Width: the stereo stage
- **Kick, snare body, sub: dead center.** No exceptions.
- **Hats and shakers: pan 10-15% L/R** (UKG convention). Stereo movement
  without compromising mono compatibility.
- **Top loops / breaks: keep the low-mids centered, widen the highs.** Use
  Mid-Side EQ to boost +2-3 dB above 5 kHz on the sides only. The break
  feels wide and airy without losing its low-end punch.
- **Mono-check constantly.** If the top loop disappears in mono, you've
  widened too aggressively or you have phase issues between break elements.

### Height: frequency distribution
- High-pass non-kick/bass elements at 80-150 Hz. Even a tiny amount of
  low-end mud in a top loop steals headroom from the sub.
- Reserve specific zones: kick body 60-100 Hz, bass 100-300 Hz, snare body
  150-250 Hz, top loop air 5-12 kHz. Each lives in its zone; they don't
  fight.

### Depth (front/back): reverb, pre-delay, tone
- **Front (close)**: high volume, full top end, longer pre-delay (20-40 ms),
  drier.
- **Back (far)**: lower volume, low-pass filtered (less highs), 0 ms
  pre-delay, more wet.
- **Send-not-insert reverb.** Always use Return Tracks so you can EQ the
  reverb itself (cut lows so it doesn't muddy, cut highs so it sits behind).

---

## V. Top loops — the Avaion-style 3D drum bed

In modern melodic deep house (Avaion, Hayden James, James Hype era), the
**top loop** does most of the heavy lifting for groove and 3D texture. It's
not just decoration — it's the rhythmic spine.

### What a top loop typically contains
- Shakers, tambourines, hats (closed and open)
- Crackle, vinyl, foley textures
- Light percussion (rim, woodblock, bongos)
- Sometimes a chopped break, low-passed and short

### How to make a top loop feel 3D

1. **Layer 2-3 loops, each panned slightly differently.** Loop A center,
   Loop B 15% L, Loop C 10% R. Each loop is a different texture (e.g.
   shaker, crackle, hat).
2. **Different EQ shapes per layer.** Shaker layer: high-pass at 200 Hz,
   slight 8 kHz boost. Crackle layer: high-pass at 1 kHz, slight 12 kHz air
   boost. Break layer: band-passed 200 Hz - 4 kHz, low-mid focused.
3. **Sidechain duck top loops gently from the kick** (1-2 dB GR). Just
   enough to give the kick room without breaking the top loop's groove.
4. **Send all top loops to a shared "Tops" bus.** Apply on that bus:
   gentle bus compression (1 dB GR), tape saturation, and a stereo widener
   that **only widens above 5 kHz** (Mid-Side EQ or a band-limited widener).
5. **Reverb on a return track**, not insert. Short-medium plate (~1.2-1.8 s),
   pre-delay ~25 ms, low-cut at 300 Hz, high-cut at 8 kHz. Send each top
   loop layer at slightly different amounts so they sit at different depths.

### Result
The top loops feel like they're happening **around** the listener rather
than in front. That's the 3D quality the user is chasing.

---

## VI. Genre-specific notes

### UK Garage (Sammy Virji / Notion lineage)

- **Broken drums = chopped break + programmed kit.** The break (often a
  slowed/pitched funk break around 130-138 BPM) carries human swing. The
  programmed kick + snare on top carry impact. Bus them together with
  parallel comp + tape sat.
- **Top loops at 130-138 BPM** with slight 60-66% groove templates on hats
  and percussion only. Kick stays straight.
- **Notion's high-energy approach**: faster mix transitions, denser top
  layers. He blends bassline, jungle, and DnB elements into the UKG
  framework — which means his top loops often borrow from breaks culture.
- **Virji's signature**: dry, percussive vocal chops sit on top of the loop
  bed — they're the 4th rhythmic element after kick, sub, and tops.

### Trap / Drill

- **Knock comes from the 808+kick relationship**, not from layering top
  loops the way UKG does. Top loops in trap are sparse — usually just hats
  and the occasional shaker fill.
- **Saturation on the 808 is the warmth.** A trap drum bus with too much
  tape sat will smear the kick transient and lose drill/trap's signature
  bite.
- **Drill specific**: keep the snare on beat 3 dry-ish — short plate at
  most. Long reverb destroys halftime impact.

### Deep house / melodic house (Avaion territory)

- **Top loops are the single most important element after kick and bass.**
  More than vocal, more than synth — the top loop establishes the genre.
- Avaion-style productions lean on:
  - Live-recorded shakers and percussion (or high-quality samples that
    sound live, like Vandalism's *HQ DRUMS: Melodic Deep House* pack)
  - Vinyl crackle and foley layers for warmth
  - Wide stereo image with mono-locked low-mids
  - Reverb sends with **lots of pre-delay** to keep the loops feeling close
    while the room sounds large
- Avaion productions often have **drum-only sections** where claps, shakers,
  and top loops carry arrangement responsibility on their own — meaning the
  loop bed has to be interesting enough to stand alone.

---

## VII. Quick checklist for the assistant

When suggesting drum mix moves, prefer in this order:

1. **Subtractive EQ first** to clean buildup (high-pass, low-mid cuts).
2. **Layer/phase fixes** if multiple drum layers are present.
3. **Saturation/parallel comp** for warmth and body.
4. **Stereo width via M/S EQ**, only above 5 kHz, only on top loops.
5. **Reverb sends with pre-delay** for depth.
6. **Volume/pan fine-tuning** last.

When the user's reference is from UKG (Virji, Notion), House/Deep House
(Avaion), Drill, or Trap, weight suggestions toward that genre's drum
philosophy as described above.
