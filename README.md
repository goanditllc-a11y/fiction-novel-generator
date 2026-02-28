# Fiction Novel Editor

A full-featured **Windows desktop application** for writing and editing large fiction novels — runs entirely locally on your computer with no cloud or API calls required.

![Fiction Novel Editor Screenshot](assets/icon.png)

---

## Features

- **Large Novel Support** — handles 500,000+ word documents via efficient `QPlainTextEdit`
- **Multi-format File Support** — open and save `.txt`, `.docx` (python-docx), and `.md` files
- **Chapter Navigation Panel** — auto-detects chapter headings (`Chapter 1`, `CHAPTER ONE`, `Part I`, `Prologue`, etc.) and lists them for one-click navigation
- **Rich Text Editing** — find & replace with regex, undo/redo, font size controls, line spacing
- **Word / Character / Page Count** displayed live in the status bar
- **Auto-save** — configurable interval, keeps the last 5 rotated backups
- **Recent Files** list (last 10 files)
- **Dark & Light themes** — toggle from the View menu
- **Drag & drop** file opening
- **AI Prompt Editing** — select text, type a natural-language instruction (e.g. *"Make this more suspenseful"*) and apply it using a local `flan-t5-base` transformer model — no internet required after first download
- **Before/After Diff Viewer** — review AI edits before accepting or rejecting
- **De-AI / Humanize Tool** — comprehensive suite to detect and remove AI writing traces:
  - Rule-based AI scoring (0–100 %)
  - Overused AI phrase detection & replacement
  - Contraction insertion (`do not` → `don't`)
  - Sentence-length variety analysis
  - Repetitive sentence-start detection
  - DOCX metadata cleaning (author, revision history, software markers)
  - Style humanisation (varied openings, voice consistency check)
  - Batch processing with full change report

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Windows 10 / 11 (64-bit) |
| Python | 3.10 or newer |
| RAM | 4 GB (8 GB recommended for AI features) |
| Disk | ~2 GB free (for local transformer model) |

---

## Installation (from source)

```bash
# 1. Clone the repository
git clone https://github.com/goanditllc-a11y/fiction-novel-generator.git
cd fiction-novel-generator

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Download the spaCy language model
python -m spacy download en_core_web_sm

# 5. Run the application
python -m src.main
```

On first use of the AI Prompt Editor the app will automatically download `flan-t5-base` (~900 MB) into `%APPDATA%\FictionNovelEditor\models\`.

---

## Building the Windows Executable

```bat
build.bat
```

This runs PyInstaller with `app.spec` and places the output in `dist\FictionNovelEditor\`.
A desktop shortcut can be created by pointing to `dist\FictionNovelEditor\FictionNovelEditor.exe`.

---

## Usage Guide

### Opening a file
- **File → Open** or drag a `.txt`, `.docx`, or `.md` file onto the window.

### Navigating chapters
The left panel automatically lists all detected chapter headings.  Click any entry to jump to that section.  Use **View → Toggle Chapter Panel** to hide/show it.

### Find & Replace
- **Edit → Find & Replace** (or `Ctrl+H`) opens the dialog.
- Supports literal text, whole-word matching, and full **regular expressions**.

### AI Prompt Editing
1. Select a passage in the editor.
2. Open **Tools → AI Prompt Editor** (or `Ctrl+P`).
3. Type a natural-language instruction and click **Apply**.
4. Review the before/after diff and choose **Accept** or **Reject**.

### De-AI / Humanize
Open **Tools → De-AI / Humanize → Batch Process** (or click the **De-AI** toolbar button).  
Check the steps you want to run, then click **Run Analysis**.  A report is generated showing every change made.

### Themes
Switch between dark and light themes via **View → Dark Theme** / **View → Light Theme**.

---

## Project Structure

```
fiction-novel-generator/
├── README.md
├── requirements.txt
├── setup.py
├── build.bat
├── app.spec
├── assets/
│   ├── icon.ico
│   ├── icon.png
│   └── generate_icons.py
├── src/
│   ├── main.py
│   ├── app.py
│   ├── editor/
│   │   ├── text_editor.py
│   │   ├── chapter_navigator.py
│   │   ├── find_replace.py
│   │   └── stats.py
│   ├── ai_editor/
│   │   ├── model_manager.py
│   │   ├── prompt_editor.py
│   │   └── diff_viewer.py
│   ├── deai/
│   │   ├── detector.py
│   │   ├── phrase_cleaner.py
│   │   ├── structure_analyzer.py
│   │   ├── metadata_cleaner.py
│   │   ├── humanizer.py
│   │   └── batch_processor.py
│   ├── file_io/
│   │   ├── file_handler.py
│   │   └── autosave.py
│   └── utils/
│       ├── config.py
│       └── constants.py
└── tests/
    ├── test_detector.py
    ├── test_phrase_cleaner.py
    ├── test_file_handler.py
    └── test_chapter_navigator.py
```

---

## Running the Tests

```bash
pytest tests/ -v
```

All tests are pure-Python and do not require a display or PyQt6 to be installed.

---

## License

MIT