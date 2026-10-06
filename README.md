# 📘 Adaptive Study Assistant

An accuracy-first, evidence-based learning assistant that transforms your course materials into interactive Obsidian study vaults and pairs them with terminal-based active retrieval sessions.

---

## 🌟 Key Features

- **📚 Course-Grounded RAG:** Ingests textbooks, lecture notes, and PDFs from `material/` and strictly grounds all instruction in your authoritative sources.
- **💎 Obsidian Knowledge Vault:** Automatically generates renderable Mermaid dependency charts, visual ASCII concept models, interactive checkboxes, and collapsible callout flashcards in `md/`.
- **🎯 Dynamic Knowledge Boundary Discovery:** Probes foundational concepts progressively, pinpointing your exact learning frontier without overwhelming you.
- **🔄 Bidirectional Obsidian Sync:** Any notes, questions, or doubts you jot down in `md/03_STUDENT_OBSIDIAN_SCRATCHPAD.md` are automatically read and brought into your next terminal dialogue.
- **⚡ Dual Terminal Chat:** Run via `aichat` REPL or native Python dialogue loop with zero configuration. Works with local CLI models or direct provider API keys (Gemini, OpenAI, Anthropic, Groq).

---

## 🚀 Quickstart

### 1. Prerequisites

- **Python:** 3.8 or higher.
- **PDF Extraction (Optional, for PDF ingestion):** `poppler-utils`
  ```bash
  # Ubuntu / Debian
  sudo apt-get install -y poppler-utils

  # macOS
  brew install poppler
  ```
- **AIChat (Optional, for advanced REPL):**
  ```bash
  cargo install aichat
  # or: brew install aichat
  ```

### 2. Launching

Clone the repository and run:

```bash
# Interactive menu
./learn

# Or using the shell wrapper
./start.sh
```

---

## 🧭 Step-by-Step Study Workflow

```
1. Add Materials        2. Index               3. Placement Check       4. Review Vault          5. Interactive Chat
┌──────────────┐       ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Put PDF/txt  │ ───>  │   ./learn    │ ───>│     ./learn      │ ───>│ Open md/ in      │ <──>│     ./learn      │
│ in material/ │       │  materials   │     │      check       │     │ Obsidian         │     │      chat        │
└──────────────┘       └──────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Step 1: Add Your Materials
Place your course notes, textbooks, or readers into `material/<subject_name>/`:
```bash
mkdir -p material/linear_algebra
cp notes.pdf textbook.txt material/linear_algebra/
```

### Step 2: Index Materials
Run the material ingestion engine to extract and index sections:
```bash
./learn materials
```

### Step 3: Find Your Starting Point
Take the adaptive placement check to pinpoint where your understanding currently sits:
```bash
./learn check
```

### Step 4: Open Your Notes in Obsidian
1. Open Obsidian.
2. Select **"Open folder as vault"** and choose the `md/` directory.
3. Browse:
   - `00_INDEX_DASHBOARD.md` — Progress tracker and topic checklist.
   - `01_CURRICULUM_ROADMAP.md` — Mermaid flowchart and visual concept models.
   - `02_BOUNDARY_CALIBRATION.md` — Diagnostic history and learning edge.
   - `03_STUDENT_OBSIDIAN_SCRATCHPAD.md` — Your personal scratchpad for questions.
   - `modules/` — Detailed lesson guides and active recall drill cards.

### Step 5: Practice in the Terminal
```bash
./learn chat
```
The tutor will guide you through exercises based on your textbook, answering any questions you left in your Obsidian scratchpad.

---

## 📂 Repository Structure

```
.
├── material/                  # Drop course readers, lecture notes, and PDFs here
│   └── spanish/               # Included sample Spanish course reader
├── md/                        # Obsidian vault directory
│   ├── 00_INDEX_DASHBOARD.md  # Main dashboard and module index
│   ├── 01_CURRICULUM_ROADMAP.md # Mermaid flowchart & visual models
│   ├── 02_BOUNDARY_CALIBRATION.md # Knowledge frontier calibration log
│   ├── 03_STUDENT_OBSIDIAN_SCRATCHPAD.md # Student scratchpad & sync notes
│   └── modules/               # Unit lessons and collapsible self-checks
├── assistant/                 # Core Python backend
│   ├── rag_manager.py         # Document extraction and BM25 RAG indexer
│   ├── boundary_search.py     # Ascending & oscillating diagnostic probe
│   ├── curriculum_planner.py  # Mermaid and roadmap generator
│   ├── obsidian_sync.py       # Scratchpad sync and note reader
│   ├── terminal_chat.py       # Terminal chat runner & REPL fallback
│   └── ai_tutor.py            # AI bridge server and prompt formatter
├── .aichat/                   # AIChat configuration, roles, and RAG profiles
├── learn                      # CLI entrypoint executable
├── start.sh                   # Convenience bash launcher
├── requirements.txt           # Dependency guide
├── .env.example               # Template for API keys
└── LICENSE                    # MIT License
```

---

## ⚙️ Configuration & API Keys

The assistant works out-of-the-box using the local CLI bridge.

To enable **instant, sub-second streaming** with external providers, copy `.env.example` to `.env` or export any of the following environment variables:

```bash
export GEMINI_API_KEY="your-gemini-key"
# or: export OPENAI_API_KEY="your-openai-key"
# or: export ANTHROPIC_API_KEY="your-anthropic-key"
# or: export GROQ_API_KEY="your-groq-key"
```

---

## 🛠️ Command Reference

| Command | Action |
| :--- | :--- |
| `./learn` | Opens the interactive command menu. |
| `./learn check` | Runs the adaptive placement diagnostic. |
| `./learn chat` | Starts an interactive study session in the terminal. |
| `./learn roadmap` | Rebuilds and updates the Obsidian study roadmap. |
| `./learn progress` | Displays current topic mastery progress. |
| `./learn notes` | Displays synced notes from your Obsidian scratchpad. |
| `./learn materials` | Re-indexes all files in `material/`. |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
