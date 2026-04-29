# AI Mixing Assistant

Analyzes reference tracks with `librosa`, asks Claude for mixing suggestions, and sends parameter changes to Ableton Live over OSC.

## What's in here

```
ai-mixer/
├── setup.sh              # one-command macOS installer
├── requirements.txt      # Python libraries
├── src/
│   ├── analyzer.py       # librosa-based feature extraction
│   ├── ableton_osc.py    # python-osc client for AbletonOSC
│   ├── ai.py             # Claude suggestion engine
│   └── app.py            # Streamlit UI
├── references/           # drop reference tracks here (gitignored)
└── tests/
```

---

## Part 1 — Install Python and the libraries (on your Mac)

You'll run **one** command in Terminal. It installs Homebrew (if missing), Python 3.11, ffmpeg, and all Python libraries into a self-contained folder called `.venv` inside this project. Nothing gets installed system-wide that you can't undo by deleting the folder.

### Step 1. Open Terminal

Press `Cmd + Space`, type `Terminal`, press Return.

### Step 2. Go to this project folder

Copy and paste this into Terminal, then press Return:

```bash
cd ~/Isaiah-portfolio/ai-mixer
```

(If you cloned the repo somewhere else, replace `~/Isaiah-portfolio` with that path.)

### Step 3. Run the setup script

```bash
bash setup.sh
```

You'll see four steps print as they run. The first time, this can take **5–15 minutes** (Homebrew + Python + librosa's audio dependencies are big). Subsequent runs are quick.

If macOS asks for your password during Homebrew install, that's normal — type it and press Return. (Letters won't appear as you type. That's also normal.)

### Step 4. Confirm it worked

When it finishes you'll see "Setup complete." Test the Streamlit app:

```bash
source .venv/bin/activate
streamlit run src/app.py
```

A browser tab should open at `http://localhost:8501`.

### Step 5. Set your Anthropic API key

Get a key at https://console.anthropic.com/. Then in Terminal:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Add that line to `~/.zshrc` if you want it set every time you open Terminal.

---

## Part 2 — Install AbletonOSC (manual, inside Ableton)

AbletonOSC is a MIDI Remote Script that lets external programs control Live over OSC. Ableton requires you to drop it into a specific folder and select it in Preferences. Here's exactly what to click.

### Step 1. Download AbletonOSC

1. Open https://github.com/ideoforms/AbletonOSC in your browser.
2. Click the green **Code** button → **Download ZIP**.
3. Open your **Downloads** folder. Double-click `AbletonOSC-master.zip` to unzip it. You'll get a folder called `AbletonOSC-master`.
4. **Rename that folder to `AbletonOSC`** (right-click → Rename). The folder name matters — Ableton won't find it otherwise.

### Step 2. Put it in Ableton's MIDI Remote Scripts folder

Ableton has two possible locations. Use the one that matches your install.

**For Ableton Live 11 or 12 (standard install):**

1. In Finder, press `Cmd + Shift + G` (Go to Folder).
2. Paste this path and press Return:
   ```
   /Users/Shared/Ableton/Live Reports/Listings
   ```
   *(If that folder is empty or doesn't exist, use the alternate location below.)*

**Alternate / recommended location** — works for all versions:

1. Open Finder. In the menu bar, click **Go → Applications**.
2. Find **Ableton Live 12 Suite** (or whichever version you have). **Right-click it → Show Package Contents**.
3. Navigate into: `Contents/App-Resources/MIDI Remote Scripts/`
4. Drag the `AbletonOSC` folder you renamed in Step 1 into this folder. macOS will ask for your password — enter it.

> **Tip:** if editing inside the app bundle feels risky, the safer alternative is the User Library:
> `~/Music/Ableton/User Library/Remote Scripts/`
> Create the `Remote Scripts` folder if it doesn't exist, then drop `AbletonOSC` inside. Ableton 11+ picks it up from there.

### Step 3. Enable it inside Ableton Live

1. **Quit Ableton Live completely** (Cmd + Q), then reopen it. It needs a fresh start to see the new script.
2. In the top menu bar: **Live → Settings…** (older versions: **Live → Preferences…**).
3. Click the **Link, Tempo & MIDI** tab (it might be called **Link / MIDI**).
4. Look at the **Control Surface** dropdowns on the right. In the first empty row:
   - **Control Surface:** select `AbletonOSC`
   - **Input:** leave as `None`
   - **Output:** leave as `None`
5. Close the Settings window.

### Step 4. Confirm it's listening

In the bottom-right status bar of Ableton you should briefly see a message like *"AbletonOSC: Listening for OSC on port 11000"*.

If you missed it, open Ableton's log:

- In Finder, press `Cmd + Shift + G` and paste:
  ```
  ~/Library/Preferences/Ableton
  ```
- Open the most recent `Live x.x.x` folder, then `Log.txt`. Search for `AbletonOSC`.

### Step 5. Test the connection

With Ableton open and a Live Set loaded, in Terminal run:

```bash
cd ~/Isaiah-portfolio/ai-mixer
source .venv/bin/activate
python -c "from src.ableton_osc import AbletonClient; AbletonClient().set_track_volume(0, 0.7)"
```

The volume fader on track 1 in Ableton should jump. If it does, you're connected.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `bash: brew: command not found` after install | Close and reopen Terminal, then re-run `bash setup.sh`. |
| `setup.sh` fails on `librosa` | Run `brew install libsndfile` then re-run `bash setup.sh`. |
| AbletonOSC doesn't appear in the Control Surface dropdown | The folder name must be exactly `AbletonOSC` (no `-master` suffix). Restart Ableton after fixing. |
| Test command runs but no fader moves | Make sure a Live Set is open with at least one track, and that Ableton is the frontmost app. |
| `ANTHROPIC_API_KEY` not set | Run `export ANTHROPIC_API_KEY="sk-ant-..."` in the same Terminal window. |

---

## Daily use

```bash
cd ~/Isaiah-portfolio/ai-mixer
source .venv/bin/activate
streamlit run src/app.py
```
