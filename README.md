# Fiction Novel Generator

A Windows desktop application that turns a simple text prompt into a full-length fiction novel using Google's Gemini AI. Built with Python and Tkinter — no coding experience required to use it.

---

## What It Does

1. You type a novel idea (e.g., *"A detective in 1920s Paris who can hear the last thoughts of murder victims"*)
2. Choose a genre and number of chapters
3. Click **Research & Generate Novel**
4. The app researches your topic, builds a world, creates characters, plots the story, and writes every chapter
5. Read the novel in the preview pane, then save it to your computer

---

## Screenshots

**Main window layout:**
- Left panel: idea input, genre/chapter settings, progress log
- Right panel: full scrollable novel preview

---

## Prerequisites

- **Python 3.9 or newer** — download at https://www.python.org/downloads/
  - ⚠️ During installation, check **"Add Python to PATH"**
- **A free Gemini API key** — get one at https://aistudio.google.com/app/apikey

---

## Quick Start (Windows)

### First-time setup

1. Download or clone this repository to a folder on your computer
2. Open that folder in File Explorer
3. **Double-click `setup_and_run.bat`**
   - It checks Python, creates a virtual environment, installs packages, and asks for your API key
   - The app opens automatically when setup completes

### Subsequent launches

- Double-click **`Novel_Generator.bat`** to open the app directly

### Optional: Desktop shortcut

- Double-click **`create_shortcut.bat`** once to add a shortcut to your desktop

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
| *"No Gemini API key found"* | Click ⚙ Settings and enter your key, or edit the `.env` file |
| *"Failed to install dependencies"* | Run Command Prompt as Administrator and re-run `setup_and_run.bat` |
| App window is blank or crashes | Make sure you're using Python 3.9+ (`python --version`) |
| Generation takes a long time | Normal — each chapter makes multiple API calls. A 10-chapter novel may take 5–15 minutes |
| API quota exceeded | You've hit the free-tier limit. Wait or upgrade your Google AI Studio plan |

---

## Requirements

- Python 3.9+
- `google-generativeai >= 0.8.0`
- `python-dotenv >= 1.0.0`
- Tkinter (included with standard Python installation)

---

## License

This project is provided for personal and educational use.