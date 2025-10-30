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
git clone https://github.com/<your-username>/promptscribe.git
cd promptscribe
pip install -e .
