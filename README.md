# PromptScribe

**PromptScribe** is a Python-based terminal session recording and analysis tool.

It captures command-line activity in a structured format so terminal sessions can be reviewed, exported, indexed, and analyzed later.

The project is focused on semantic terminal logging rather than full terminal replay.

---

## Status

Active development.

Current stable focus:

- Linux-based terminal recording
- structured command/session logging
- metadata tracking
- SQLite session indexing
- raw text export
- GUI-based session browsing

Tested primarily in Linux Virtual Machine environments.

Windows and macOS support are planned/experimental and may require additional validation.

---

## Features

- **Session Recording**  
  Capture terminal command activity and output into structured JSONL logs.

- **Metadata Tracking**  
  Store session ID, description, timestamps, and log file path.

- **SQLite Indexing**  
  Index recorded sessions for later lookup and management.

- **Raw Log Export**  
  Export recorded sessions into readable `.txt` files.

- **GUI Viewer**  
  Browse recorded sessions with a graphical interface.

- **Local-Only Storage**  
  Session data is stored locally under the project `data/` directory.

- **Semantic Logging Focus**  
  Designed for structured analysis of terminal sessions rather than byte-perfect terminal replay.

---

## Project Structure

```text
promptscribe/
├── promptscribe/
│   ├── cli.py
│   ├── recorder.py
│   ├── session.py
│   ├── scraper.py
│   ├── db.py
│   ├── gui.py
│   └── ...
├── data/
│   ├── logs/
│   ├── metadata/
│   ├── database/
│   └── exports/
├── docs/
├── experiments/
├── README.md
├── requirements.txt
├── pyproject.toml
└── setup.py
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/nittsOG/promptscribe.git
cd promptscribe
```

---

### 2. Create a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

After activation, the terminal should show:

```text
(.venv)
```

---

### 3. Upgrade pip

```bash
pip install --upgrade pip
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Install PromptScribe in editable mode

```bash
pip install -e .
```

This registers the `promptscribe` command.

Verify installation:

```bash
promptscribe --help
```

---

## Database Initialization

Before recording or indexing sessions, initialize the database:

```bash
promptscribe db init
```

This creates the local data structure:

```text
data/
├── logs/
├── metadata/
├── database/
└── exports/
```

---

## Basic Usage

### Record a terminal session

```bash
promptscribe record --desc "test session"
```

During recording:

```text
stoprec
```

ends the recording session.

If supported by the current recorder mode:

```text
:kill
```

interrupts the currently running command without ending the recording session.

---

### Export a recorded session

Export/scrape a session by description:

```bash
promptscribe scrape --desc "test session"
```

The exported text file is saved under:

```text
data/exports/
```

---

### Launch the GUI

```bash
promptscribe gui
```

---

### Show help

```bash
promptscribe --help
```

---

## How PromptScribe Works

PromptScribe follows a structured recording pipeline:

```text
Terminal session
      ↓
Recorder
      ↓
Structured JSONL log
      ↓
Session metadata
      ↓
SQLite index
      ↓
Scraper / Viewer / GUI
```

Recorded sessions are stored as JSONL event logs.  
Each event can include timestamped input, output, signal, or session metadata.

This design makes sessions easier to:

- inspect
- export
- search
- analyze
- extend in future tooling

---

## Data Storage

PromptScribe stores runtime data locally.

```text
data/logs/        JSONL session logs
data/metadata/    session metadata files
data/database/    SQLite database files
data/exports/     exported readable text logs
```

No external network service is required for core recording and local analysis.

---

## Development Workflow

Recommended development flow:

```bash
git checkout main
git pull
git checkout -b feature/your-feature-name
```

Make changes, then:

```bash
git status
git add .
git commit -m "type(scope): short description"
git push -u origin feature/your-feature-name
```

Suggested commit style:

```text
feat(recorder): add new recording behavior
fix(db): correct initialization path
docs(readme): update installation instructions
experiment(shell): evaluate persistent shell behavior
```

---

## Documentation

Project documentation is stored under:

```text
docs/
```

Experimental research and architecture notes may also be stored under:

```text
experiments/
```

---

## Current Limitations

PromptScribe currently focuses on structured semantic logging.

It is not intended to be a byte-perfect terminal recorder like traditional terminal replay tools.

Known limitations:

- full-screen terminal applications may not record perfectly
- interactive TUI programs may behave differently
- terminal behavior can vary across shells and environments
- Windows/macOS support requires further validation
- persistent shell and PTY-backed modes are experimental/future work

---

## Roadmap

Possible future improvements:

- improved input handling
- better command boundary detection
- richer GUI filtering
- session search improvements
- export formats beyond raw text
- optional PTY-backed recording mode
- persistent shell mode research
- test suite and CI integration
- packaged release distribution

---

## Release Notes

Current release notes are available in:

```text
RELEASE_NOTES.md
```

---

## License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.

---

## Repository

GitHub:

```text
https://github.com/nittsOG/promptscribe
```
