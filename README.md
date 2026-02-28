# Fiction Novel Generator

A Windows desktop application that turns a simple text prompt into a full-length fiction novel — a **minimum of 350 pages** (~87,500 words). Research is done automatically using free online resources. Novel generation runs entirely on your local PC. **No API key required.**

---

## ⬇️ Download the App

### ✅ Download Now (works immediately)

**[⬇️ Download fiction-novel-generator.zip](https://github.com/goanditllc-a11y/fiction-novel-generator/releases/latest/download/fiction-novel-generator.zip)**

Click the link — the ZIP downloads instantly, no login required.

### After downloading

1. **Extract** the ZIP anywhere on your PC (right-click → *Extract All…*) — e.g. `Downloads\fiction-novel-generator`
2. **Double-click `install.bat`** inside the extracted folder *(recommended)*
   - A black Command Prompt window opens — this is normal
   - It installs Python packages, copies the app to your user folder, and creates **Desktop + Start Menu shortcuts**
3. The **Fiction Novel Generator** window opens ✅
4. Next time, open the app from your **Desktop** or the **Start Menu** — no need to find the ZIP again

> **Alternative (no install):** Double-click `setup_and_run.bat` to run the app directly from the extracted folder.

> **No API key needed.** Research uses the free Wikipedia API. For author-quality prose, optionally install [Ollama](https://ollama.ai) and run `ollama pull llama3.2`.

Full step-by-step instructions are in the [Quick Start](#quick-start-windows) section below.

### Other download options

| Option | Link | Notes |
|--------|------|-------|
| **GitHub Releases** *(above)* | [releases/latest](https://github.com/goanditllc-a11y/fiction-novel-generator/releases/latest) | Always up-to-date, no login needed |
| **Branch ZIP** | [fiction-novel-generator.zip][zip-branch] | Direct branch archive |
| **Actions artifact** | [Actions tab → latest run → Artifacts](https://github.com/goanditllc-a11y/fiction-novel-generator/actions/workflows/release.yml) | `fiction-novel-generator` artifact, kept 90 days |

[zip-branch]: https://github.com/goanditllc-a11y/fiction-novel-generator/archive/refs/heads/copilot/build-fiction-novel-generator.zip

---

## What It Does

1. You type a novel idea (e.g., *"A detective in 1920s Paris who can hear the last thoughts of murder victims"*)
2. Choose a genre and number of chapters (default: 25 chapters ≈ 350+ pages)
3. Click **Research & Generate Novel**
4. The app researches your topic via Wikipedia, builds a world, creates characters, plots the story arc, and writes every chapter
5. Read the novel in the preview pane, then save it to your computer
6. **Optionally:** click **✏️ Rewrite Novel…** to apply a style prompt ("make it more literary", "make it darker", etc.) — the original is auto-saved and you pick which version to keep
7. **Optionally:** click **✍️ Generate Sequels…** to produce 1–5 independent sequel drafts and choose the best one

---

## How Generation Works

| Stage | What happens | Where it runs |
|-------|-------------|--------------|
| **Research** (Phase 1) | Searches Wikipedia for your topic — historical context, genre conventions, thematic ideas | Internet (free Wikipedia API, no key needed) |
| **Characters, World, Plot** (Phases 2–5) | Builds a full cast, world bible, and chapter-by-chapter outline | **Your PC — no internet** |
| **Chapter Writing** (Phase 6) | Writes 25+ full chapters (~3,500 words each) | **Your PC — Ollama LLM if installed; built-in generator otherwise** |
| **Compile** (Phase 7) | Assembles everything into the final novel document | **Your PC** |

### Generation quality modes

| Mode | How to activate | Prose quality | Pages |
|------|----------------|--------------|-------|
| **Ollama LLM** *(recommended)* | Install [Ollama](https://ollama.ai) + pull a model | Author-level literary prose | 350+ |
| **Built-in generator** | Works out of the box, no install | Structured story-driven prose | 350+ |

---

## Installing Ollama (for author-quality prose)

Ollama runs open-weight AI language models (Llama 3, Mistral, Phi-3, etc.) entirely on your PC. No data leaves your machine. No subscription. Free.

1. Go to **https://ollama.ai/download** and download the Windows installer
2. Run the installer — Ollama starts as a background service automatically
3. Open **Command Prompt** and run:
   ```
   ollama pull llama3.2
   ```
   This downloads the model (~2 GB) once.  It stays on your PC forever.
4. Open the Fiction Novel Generator — it will detect Ollama automatically and show **✅ Ollama ready** in the status bar

**Recommended models** (best → smallest):

| Model | Size | RAM needed | Command |
|-------|------|-----------|---------|
| `llama3.1:8b` | 5 GB | 8 GB | `ollama pull llama3.1:8b` |
| `mistral` | 4 GB | 8 GB | `ollama pull mistral` |
| `llama3.2` | 2 GB | 4 GB | `ollama pull llama3.2` ← recommended starter |
| `phi3:mini` | 1 GB | 2 GB | `ollama pull phi3:mini` |

---

## Screenshots

**Main window layout:**
- Top bar: Ollama status indicator + Refresh button
- Left panel: idea input, genre/chapter settings, progress log
- Right panel: full scrollable novel preview (~350+ pages)

---

## Prerequisites

- **Python 3.9+** — free from https://www.python.org/downloads/  
  *(all other dependencies install automatically — see Quick Start)*
- **Internet connection** — needed only for the research phase (Wikipedia). Novel generation itself is fully offline.
- **Ollama** *(optional)* — for author-quality prose. See [Installing Ollama](#installing-ollama-for-author-quality-prose) above.

---

## Quick Start (Windows)

### Step 1 — Install Python (one-time, skip if already done)

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. ⚠️ On the first screen, tick the box **"Add Python to PATH"** before clicking Install Now
5. Click **Install Now** and wait for it to finish

### Step 2 — Download this app

**[⬇️ Click here to download fiction-novel-generator.zip](https://github.com/goanditllc-a11y/fiction-novel-generator/releases/latest/download/fiction-novel-generator.zip)** — saves to your Downloads folder automatically

### Step 3 — Extract the ZIP

1. Open your **Downloads** folder in File Explorer
2. Right-click the downloaded ZIP file
3. Choose **"Extract All…"**
4. Choose a destination folder (e.g. `C:\Users\YourName\Downloads`) and click **Extract**
5. Open the extracted folder — you should see files like `install.bat`, `setup_and_run.bat`, `main.py`, etc.

### Step 4 — Install (one-time)

1. Inside the extracted folder, **double-click `install.bat`**
   - A black Command Prompt window opens — this is normal
   - It checks Python, copies the app to `%USERPROFILE%\FictionNovelGenerator`, installs packages, and creates Desktop + Start Menu shortcuts
2. The app window opens automatically when setup is complete 🎉

### Launching the app after the first time

- Open from your **Desktop** — double-click **Fiction Novel Generator**
- Or open from the **Start Menu** — search "Fiction Novel Generator"
- Or double-click **`Novel_Generator.bat`** in the install folder directly

### Optional: Pin a shortcut to your Desktop

If you skipped the installer and used `setup_and_run.bat` instead:
- Double-click **`create_shortcut.bat`** once — it adds a **"Fiction Novel Generator"** icon to your Desktop

---

## How to Use the App

| Control | Description |
|---------|-------------|
| **Novel Idea / Concept** | Type your story idea here — the more detail, the better |
| **Genre** | Choose from 10 genres (Fantasy, Sci-Fi, Mystery, Romance, etc.) |
| **Chapters** | Pick 1–50 chapters (default 25; each chapter ~3,500 words ≈ 350+ pages total) |
| **Research & Generate Novel** | Starts the 7-phase generation pipeline |
| **Status / Progress** | Shows live updates as each phase completes |
| **Novel Preview** | Displays the finished novel — scrollable and readable |
| **Save Novel** | Saves to `novels/YYYY-MM-DD/Title/v1/` in the install folder |
| **New Novel** | Clears everything to start fresh |
| **✏️ Rewrite Novel…** | Apply a style prompt to transform the prose ("make it more literary", "make it darker and more suspenseful", etc.) — the original is auto-saved before rewriting starts, then a side-by-side comparison lets you choose which version to keep and download |
| **✍️ Generate Sequels…** | Generate 1–5 independent sequel drafts; a selection dialog shows word counts and a preview so you can pick the best one |
| **↻ Refresh** | Re-checks whether Ollama is running |
| **⚙ Settings** | Shows Ollama and research configuration |

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
            ├── research_notes.txt       ← background research (Wikipedia + genre context)
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
├── web_researcher.py    ← Free web research via Wikipedia API (no key needed)
├── ollama_generator.py  ← Local LLM chapter generation via Ollama
├── local_generator.py   ← Built-in generator (350+ pages, no Ollama required)
├── file_manager.py      ← Saves novels to the organised folder structure
├── config.py            ← All configurable settings (Ollama host, defaults, paths)
├── requirements.txt     ← Python package dependencies
├── .gitignore           ← Keeps generated files out of git
├── install.bat          ← One-click installer (copies app, creates Desktop + Start Menu shortcuts)
├── setup_and_run.bat    ← First-time setup + launcher (run-in-place alternative to install.bat)
├── Novel_Generator.bat  ← Quick launcher after first setup (Windows)
└── create_shortcut.bat  ← Creates a desktop shortcut (Windows)
```

---

## How to Extend / Add Features

The app is intentionally modular. Adding a new feature typically means:

1. **New setting** (e.g., writing style): add a variable to `config.py`, add a widget to `gui.py`, pass the value through `novel_engine.py`
2. **New genre**: open `config.py` and add the genre string to the `GENRES` list — it appears in the dropdown automatically
3. **New output file type**: add a `_write_*` method in `file_manager.py` and call it from `save_novel()`
4. **New generation phase**: add a method in `novel_engine.py` and call it from `generate_novel()`

Each file has `# TO EXTEND:` comments at key extension points.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| *"Python is not installed or not in your PATH"* | Reinstall Python from python.org and check **Add Python to PATH** |
| *"Failed to install dependencies"* | Run Command Prompt as Administrator and re-run `install.bat` |
| App window is blank or crashes | Make sure you're using Python 3.9+ (`python --version`) |
| Ollama shows "not found" | Install from https://ollama.ai/download, then run `ollama pull llama3.2` |
| Ollama "no models pulled" warning | Run `ollama pull llama3.2` in Command Prompt |
| Research uses offline fallback | Normal — Wikipedia wasn't reachable. The app still generates a complete novel. |
| Generation takes a long time | Normal with Ollama for 25 chapters — local LLM generation is thorough. Progress dots appear in the status area. |
| Rewrite shows no change | Ollama is not installed — the rewrite falls back to regeneration. Install Ollama for chapter-level style rewrites. |
| Desktop/Start Menu shortcut missing | Re-run `install.bat` or run `create_shortcut.bat` to create the Desktop shortcut only. |

---

## Requirements

- Python 3.9+
- `requests >= 2.28.0`
- `beautifulsoup4 >= 4.12.0`
- `python-dotenv >= 1.0.0`
- Tkinter (included with standard Python installation)

---

## License

This project is provided for personal and educational use.

---
