# Persistent Shell Experiment

## Status

Experimental.  
Not merged into production.  
Used for architectural evaluation and future PTY groundwork.

---

# Project Context

Part of the PromptScribe project.

PromptScribe is a structured semantic terminal recording tool focused on:
- command/session logging
- semantic replay
- command analysis
- terminal activity tracking

Repository architecture currently prioritizes:
- stable logging
- deterministic command execution
- structured event capture

---

# Goal

Evaluate replacing isolated per-command execution with a persistent shell subprocess architecture.

Primary objectives:

- Preserve shell state across commands
- Support:
  - `cd`
  - `export`
  - aliases
  - shell variables
  - command history behavior
- Improve terminal realism
- Prepare groundwork for future interactive recording support

---

# Previous Recorder Architecture

PromptScribe originally used isolated command execution:

```python
subprocess.Popen(command, shell=True)