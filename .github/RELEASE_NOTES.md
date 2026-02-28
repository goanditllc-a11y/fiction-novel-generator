## Fiction Novel Generator — Latest Release

### ⬇️ How to Download & Install

1. Click **`fiction-novel-generator.zip`** in the *Assets* section below to download
2. **Extract** the ZIP anywhere on your PC (right-click → *Extract All…*)
   - e.g. `C:\Users\YourName\Downloads\fiction-novel-generator`
3. **Double-click `install.bat`** inside the extracted folder *(recommended — installs to your user folder and creates Desktop + Start Menu shortcuts)*
   - A black Command Prompt window opens — this is normal
   - It checks Python, copies the app, installs dependencies, and creates shortcuts automatically
4. The **Fiction Novel Generator** window opens ✅
5. In future, open the app from your **Desktop** or **Start Menu**

> **Alternative:** If you want to run the app directly from the ZIP folder without installing, double-click `setup_and_run.bat` instead.

---

### Requirements

- **Windows** 10 or 11
- **Python 3.9+** — [Download free from python.org](https://www.python.org/downloads/)
  - ⚠️ During install, tick **"Add Python to PATH"**
- **Internet connection** — only needed for the research phase (Wikipedia). Generation is fully offline.

---

### What's in this release

| Feature | Details |
|---------|---------|
| **No API key required** | Research uses the free Wikipedia public API |
| **Local generation** | All novel writing runs entirely on your PC |
| **350+ pages** | 25 chapters × ~3,500 words ≈ 350 pages minimum |
| **Ollama support** | Optional — install [Ollama](https://ollama.ai) for author-quality prose |
| **✏️ Rewrite Novel** | Apply a style prompt to any generated novel ("make it more literary", "make it darker", etc.) — original auto-saved, side-by-side comparison lets you pick your preferred version |
| **✍️ Generate Sequels** | Generate 1–5 independent sequel drafts and pick the best one to keep |
| **One-click installer** | `install.bat` copies the app to your user folder and creates Desktop + Start Menu shortcuts |

---

### Optional: Author-quality prose with Ollama

For literary-grade prose (think Ursula K. Le Guin, Tana French, Gillian Flynn):

1. Download the Windows installer from **https://ollama.ai/download**
2. Run the installer
3. Open Command Prompt and run:
   ```
   ollama pull llama3.2
   ```
4. Start the app — it will detect Ollama automatically and show **✅ Ollama ready**

Recommended models: `llama3.2` (~2 GB), `mistral` (~4 GB), `llama3.1:8b` (~5 GB)

The **Rewrite Novel** feature uses Ollama to rewrite chapter-by-chapter when it is available, giving the highest-quality style transformations.

---

*Built automatically from the latest source. No API key required.*

