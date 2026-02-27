# Fiction Novel Generator

A Windows desktop application that turns a simple text prompt into a full-length fiction novel using Google's Gemini AI. Built with Python and Tkinter — no coding experience required to use it.

---

## ⬇️ Download the App

**[⬇️ Download fiction-novel-generator.zip][zip-branch]**

1. Click the link above — the ZIP file downloads automatically
2. Extract it anywhere on your PC (e.g. `Documents\fiction-novel-generator`)
3. Double-click **`setup_and_run.bat`** inside the extracted folder
4. The API key prompt is **optional** — press Enter to skip it and generate novels offline
5. The app opens automatically ✅

Full step-by-step instructions are in the [Quick Start](#quick-start-windows) section below.

[zip-branch]: https://github.com/goanditllc-a11y/fiction-novel-generator/archive/refs/heads/copilot/build-fiction-novel-generator.zip

---

## What It Does

1. You type a novel idea (e.g., *"A detective in 1920s Paris who can hear the last thoughts of murder victims"*)
2. Choose a genre and number of chapters
3. Click **Research & Generate Novel**
4. The app researches your topic, builds a world, creates characters, plots the story, and writes every chapter
5. Read the novel in the preview pane, then save it to your computer

---

## How Generation Works

The app uses a **two-stage pipeline** designed to stay within free-tier API limits:

| Stage | What happens | API calls |
|-------|-------------|-----------|
| **Research** (Phase 1) | One Gemini call gathers background context, genre conventions, and thematic ideas for your story | **1 call total** |
| **Generation** (Phases 2–7) | Characters, world, plot, chapter outlines, and full chapter prose are generated **locally on your machine** from the research | **0 calls** |

This means a 10-chapter novel uses **exactly one** API call instead of the 13+ calls the original design used — which was causing the free-tier quota error (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`).

**No API key?** The app falls back to built-in genre knowledge for the research phase and generates your novel entirely offline.

---

## Screenshots

**Main window layout:**
- Left panel: idea input, genre/chapter settings, progress log
- Right panel: full scrollable novel preview

---

## Prerequisites

- **A free Gemini API key** *(optional but recommended)* — get one at https://aistudio.google.com/app/apikey  
  Without a key the app still generates complete novels using built-in genre knowledge.  
  *(Python setup is covered in Step 1 of Quick Start below)*

---

## Quick Start (Windows)

### Step 1 — Install Python (one-time, skip if already done)

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. ⚠️ On the first screen, tick the box **"Add Python to PATH"** before clicking Install Now
5. Click **Install Now** and wait for it to finish

### Step 2 — Download this app

1. **[⬇️ Download fiction-novel-generator.zip][zip-branch]** — the file will save to your Downloads folder automatically
2. Skip to Step 3 below to extract it

### Step 3 — Extract the ZIP

1. Open your **Downloads** folder in File Explorer
2. Right-click the downloaded ZIP file
3. Choose **"Extract All…"**
4. Choose a destination folder (e.g. `C:\Users\YourName\Documents\fiction-novel-generator`) and click **Extract**
5. Open the extracted folder — you should see files like `setup_and_run.bat`, `main.py`, etc.

### Step 4 — Run the setup (first time only)

1. Inside the extracted folder, **double-click `setup_and_run.bat`**
   - A black Command Prompt window opens — this is normal
   - It checks Python, creates a virtual environment, and installs the required packages
   - When it asks for your Gemini API key, you can **paste your key and press Enter** or **just press Enter to skip**  
     *(Without a key the app still generates complete novels using built-in genre knowledge)*
2. The app window opens automatically when setup is complete 🎉

### Launching the app after the first time

- Double-click **`Novel_Generator.bat`** inside the folder — that's it

### Optional: Pin a shortcut to your Desktop

- Double-click **`create_shortcut.bat`** once — it adds a **"Fiction Novel Generator"** icon to your Desktop

---

## How to Get a Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key
5. Either:
   - Paste it when `setup_and_run.bat` asks during first-time setup, **or**
   - Open the app → click **⚙ Settings** → paste the key → click **Save**

Your key is saved in a local `.env` file and never sent anywhere except to Google's API.

---

## How to Use the App

| Control | Description |
|---------|-------------|
| **Novel Idea / Concept** | Type your story idea here — the more detail, the better |
| **Genre** | Choose from 10 genres (Fantasy, Sci-Fi, Mystery, Romance, etc.) |
| **Chapters** | Pick 1–50 chapters (default 10; each chapter ~1500–2000 words) |
| **Research & Generate Novel** | Starts the 7-phase generation pipeline |
| **Status / Progress** | Shows live updates as each phase completes |
| **Novel Preview** | Displays the finished novel — scrollable and readable |
| **Save Novel** | Saves to `novels/YYYY-MM-DD/Title/v1/` in this folder |
| **New Novel** | Clears everything to start fresh |
| **⚙ Settings** | Enter or update your Gemini API key |

---

## Output Folder Structure

Every saved novel creates the following files:

```
novels/
└── 2025-06-15/
    └── My_Novel_Title/
        └── v1/
            ├── My_Novel_Title_v1.txt    ← full plain-text novel
            ├── My_Novel_Title_v1.md     ← Markdown-formatted version
            ├── research_notes.txt       ← background research
            ├── characters.txt           ← character profiles
            ├── plot_outline.txt         ← full plot architecture
            └── metadata.json           ← title, genre, word count, etc.
```

If you generate multiple novels with the same title on the same day, versions are auto-incremented (v1 → v2 → v3 …).

---

## Project File Structure

```
fiction-novel-generator/
├── main.py              ← Entry point — run this to launch the app
├── gui.py               ← Tkinter window and all UI widgets
├── novel_engine.py      ← Orchestrates all 7 generation phases
├── researcher.py        ← AI-powered background research
├── file_manager.py      ← Saves novels to the organised folder structure
├── config.py            ← All configurable settings (model, defaults, paths)
├── requirements.txt     ← Python package dependencies
├── .env.example         ← Template for your API key file
├── .gitignore           ← Keeps secrets and generated files out of git
├── setup_and_run.bat    ← First-time setup + launcher (Windows)
├── Novel_Generator.bat  ← Quick launcher after first setup (Windows)
└── create_shortcut.bat  ← Creates a desktop shortcut (Windows)
```

---

## How to Extend / Add Features

The app is intentionally modular. Adding a new feature typically means:

1. **New setting** (e.g., writing style): add a variable to `config.py`, add a widget to `gui.py`, pass the value through `novel_engine.py`
2. **New genre**: open `config.py` and add the genre string to the `GENRES` list — it appears in the dropdown automatically
3. **New output file type**: add a `_write_*` method in `file_manager.py` and call it from `save_novel()`
4. **New generation phase**: add a `_phase_*` method in `novel_engine.py` and call it from `generate_novel()`

Each file has `# TO EXTEND:` comments at key extension points.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| *"Python is not installed or not in your PATH"* | Reinstall Python from python.org and check **Add Python to PATH** |
| *"No Gemini API key found"* | The app will use built-in genre knowledge automatically. For richer research, click ⚙ Settings and enter your free key |
| *"Failed to install dependencies"* | Run Command Prompt as Administrator and re-run `setup_and_run.bat` |
| App window is blank or crashes | Make sure you're using Python 3.9+ (`python --version`) |
| API quota error (`GenerateRequestsPerDay…`) | Already fixed — generation now runs locally; only 1 API call is made per novel |
| Generation takes a long time | Normal for large chapter counts — all generation is local so speed depends on your PC |
| API quota exceeded on research call | You've hit the free daily limit. Wait until it resets (midnight Pacific) or generate without a key |

---

## Requirements

- Python 3.9+
- `google-generativeai >= 0.8.0`
- `python-dotenv >= 1.0.0`
- Tkinter (included with standard Python installation)

---

## License

This project is provided for personal and educational use.