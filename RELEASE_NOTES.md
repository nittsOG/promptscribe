<!-- cat > RELEASE_NOTES.md <<'EOF' -->
## v1.1.0 — Recorder reliability & signal handling

### Added
- SIGINT forwarding to child process groups in PTY/fork mode.
- Subprocess fallback when PTY/fork are unavailable (works in restricted containers).
- `:kill` command to send SIGINT to the running process without ending the session.
- Groundwork for isolated/per-command mode (future --isolated flag).

### Fixed
- Ctrl+C now interrupts running command and retains recorder session.
- Improved ANSI cleaning and logging robustness.

Notes:
- `pexpect` not required for current implementation; not added to `requirements.txt`.
EOF
