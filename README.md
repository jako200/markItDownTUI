# MarkItDown TUI — Terminal UI

A modern **terminal application** for [Microsoft MarkItDown](https://github.com/microsoft/markitdown), built in Python with [Textual](https://textual.textualize.io/).  
Convert Word, PowerPoint, Excel, PDF, HTML and more to Markdown — all from your terminal, with no desktop environment required.

> **Two flavours available — pick yours:**
>
> | | Repo | Best for |
> |---|---|---|
> | 🖥️ **MarkItDown Studio** (GUI) | [github.com/jako200/markItDownGUI](https://github.com/jako200/markItDownGUI) | Desktop users, Windows / macOS / Linux with GUI |
> | 🖮 **MarkItDown TUI** (this one) | [github.com/jako200/markItDownTUI](https://github.com/jako200/markItDownTUI) | Terminal users, headless servers, SSH sessions |
>
> Both share the same conversion engine and support the same file formats.

---

## 🚀 Features

### Single File Conversion
- Input any supported file by typing its path directly
- Optional custom output destination (defaults to same folder as input)
- Real-time file info preview (format, size) as you type
- Asynchronous conversion — the TUI stays fully responsive

### Batch Conversion
- Queue files via individual paths, full directories, or glob patterns (`~/docs/*.pdf`, `reports/*.docx`)
- Automatic format validation and duplicate prevention
- Optional custom output directory (or save alongside each source file)
- Scrollable file list with per-file live status badges: `in coda` → `in corso` → `OK` / `errore`
- Progress bar with file count
- **Cancel** button to cooperatively interrupt a running batch at any time

### Built-in Log Console
- Timestamped, colour-coded log (Info / Success / Warning / Error)
- One-click clear button and `Ctrl+L` shortcut

### Design & Usability
- Consistent dark theme inspired by the Obsidian palette
- Tab-based layout (`Ctrl+T` to switch between Single and Batch)
- Keyboard shortcuts shown in the footer
- Cross-platform: Linux, macOS, Windows — any terminal

---

## 🗂️ Supported Formats

| Format | Extension(s) |
|---|---|
| Word Document | `.docx` |
| PowerPoint Presentation | `.pptx` |
| Excel Spreadsheet | `.xlsx` |
| PDF | `.pdf` |
| HTML / Web page | `.html`, `.htm` |
| Plain text / Code | `.txt`, `.csv`, `.xml`, `.json` |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + Q` | Quit the application |
| `Ctrl + T` | Switch between Single and Batch tabs |
| `Ctrl + L` | Clear the log console |

---

## 🛠️ Requirements & Installation

Requires **Python 3.8+**.

### 1. Clone the repository
```bash
git clone https://github.com/jako200/markItDownTUI.git
cd markItDownTUI
```

### 2. Create a virtual environment (recommended)

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 💻 Run the Application

```bash
python main.py
```

Or use the provided launcher scripts:
- **Linux / macOS:** `./run.sh`
- **Windows:** `run.bat`

---

## 🏗️ Project Structure

```
markItDownTUI/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies (textual, markitdown[all])
├── run.sh                  # Launcher for Linux/macOS
├── run.bat                 # Launcher for Windows
├── src/
│   ├── core/
│   │   ├── converter.py    # MarkItDown wrapper + BatchConversionWorker
│   │   └── helpers.py      # Format detection & size formatting
│   └── tui/
│       ├── app.py          # TUI app — layout, tabs, event handling
│       └── styles.py       # Obsidian dark colour palette
└── tests/
    ├── test_core.py        # Unit tests for the conversion engine
    └── test_tui.py         # Async integration tests for the Textual UI
```

---

## 🧪 Tests

Run the full test suite (18 automated tests covering both the engine and the UI):

```bash
python -m unittest discover tests
```

---

## 🔗 Related Project

Prefer a **graphical desktop application** with file-browser dialogs and a polished GUI?  
➡️ Check out [**MarkItDown Studio**](https://github.com/jako200/markItDownGUI) — same features, same engine, full CustomTkinter GUI for Windows / macOS / Linux.
