# PromptScribe

**PromptScribe** is a lightweight CLI + GUI toolkit to record, analyze, and manage terminal sessions.  
It supports multi-platform environments (Linux, Windows, macOS) and is optimized for VM or container use.

---

## 🚀 Features

- **Session Recording:** Capture shell input/output in structured JSONL format.  
- **Database Indexing:** Store, tag, and search previous sessions via SQLite.  
- **GUI Mode:** Visualize sessions with filters, metadata, and previews.  
- **Analytics:** Generate per-session stats and CSV exports.  
- **Cross-Platform:** Works with both `pty` (Unix) and `wexpect` (Windows).  
- **Secure:** Minimal dependencies, no network calls, local-only data.

---

## 🧩 Installation

### Option 1 — From Source (recommended for contributors)
```bash
git clone https://github.com/nittsOG/promptscribe.git
cd promptscribe
pip install -e .

```

---
## Virtual Environment Setup 

3. Create virtual environment
python3 -m venv .venv

Activate it.

Linux / macOS:
```
source .venv/bin/activate
```
Windows:
```
.venv\Scripts\activate
```
You should see:

(.venv)

in the terminal prompt.


---

4. Install project dependencies

Upgrade pip:
```
pip install --upgrade pip
```
Install requirements:
```
pip install -r requirements.txt
```

---

5. Install the project (editable mode)

Run from project root:
```
pip install -e .
```
This registers the CLI command promptscribe.

Verify:
```
promptscribe --help
```

---

6. Initialize the database
```
promptscribe db init
```
This creates:

data/
 ├── logs
 ├── metadata
 └── database

 ---
 
