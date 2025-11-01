import os
import sys
import time
import json
import subprocess
import platform
import signal
import re
import termios

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
STOP_CMD = "stoprec"
KILL_CMD = ":kill"

current_proc = None  # global active subprocess reference


# -------------------------
# Utility Functions
# -------------------------
def _strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)


def _clean_output(data: str) -> str:
    s = ANSI_ESCAPE_RE.sub("", data)
    s = s.replace("\b", "")
    return s


def _write_event(fh, kind, data):
    clean_data = _strip_ansi(data)
    evt = {"ts": round(time.time(), 6), "kind": kind, "data": clean_data}
    fh.write(json.dumps(evt, ensure_ascii=False) + "\n")
    fh.flush()


def _ensure_path(outpath):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if not os.path.exists(outpath):
        meta = {
            "version": "2.2",
            "platform": platform.system(),
            "start_time": time.time(),
        }
        with open(outpath, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"meta": meta}) + "\n")


# -------------------------
# Command Execution
# -------------------------
def _run_command(command, fh):
    """Run a single command in its own process group for clean signal control."""
    global current_proc
    current_proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,  # new process group
        bufsize=1,
    )

    try:
        for line in iter(current_proc.stdout.readline, ""):
            cleaned = _clean_output(line)
            sys.stdout.write(cleaned)
            sys.stdout.flush()
            _write_event(fh, "out", cleaned)
    except Exception as e:
        _write_event(fh, "error", f"cmd_output_error:{repr(e)}")
    finally:
        current_proc.wait()
        current_proc = None


def _kill_current(fh):
    """Interrupt the running command group."""
    global current_proc
    if current_proc and current_proc.poll() is None:
        try:
            os.killpg(os.getpgid(current_proc.pid), signal.SIGINT)
            _write_event(fh, "signal", "SIGINT_sent_to_child_group")
            sys.stdout.write("[Interrupted current process]\n")
            sys.stdout.flush()
        except Exception as e:
            _write_event(fh, "signal_error", f"SIGINT_failed:{repr(e)}")


# -------------------------
# SIGINT Handler
# -------------------------
def _sigint_handler(signum, frame):
    global current_proc
    if current_proc and current_proc.poll() is None:
        try:
            os.killpg(os.getpgid(current_proc.pid), signal.SIGINT)
        except Exception:
            pass
        sys.stdout.write("\n[Ctrl+C] Interrupted current command. Ready for next.]\n")
        sys.stdout.flush()
    else:
        try:
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except Exception:
            pass
        sys.stdout.write("\n[Ctrl+C received - no active process, ready for next]\n")
        sys.stdout.flush()


# -------------------------
# Recording Loop (Unix)
# -------------------------
def record_unix(outpath):
    _ensure_path(outpath)
    shell_name = os.environ.get("SHELL", "/bin/bash")

    # Register single handler for Ctrl+C
    signal.signal(signal.SIGINT, _sigint_handler)

    print(f"Recording active. Type commands below ({STOP_CMD} to stop, {KILL_CMD} to interrupt current command).")

    with open(outpath, "a", encoding="utf-8") as fh:
        _write_event(fh, "info", f"session_start:{shell_name}")
        while True:
            try:
                sys.stdout.write(os.getcwd() + " $ ")
                sys.stdout.flush()
                line = sys.stdin.readline()
                if not line:
                    break

                cmd = line.strip()
                _write_event(fh, "in", cmd + "\n")

                if cmd.lower() == STOP_CMD:
                    _write_event(fh, "session_end", f"user_command:{STOP_CMD}")
                    print("Session stopped.")
                    break

                if cmd.lower() == KILL_CMD:
                    _kill_current(fh)
                    continue

                _run_command(cmd, fh)

            except Exception as e:
                _write_event(fh, "error", f"record_loop_exception:{repr(e)}")
                break

        _write_event(fh, "session_end", "normal_exit")


# -------------------------
# Windows Backend (simplified)
# -------------------------
def record_windows(outpath):
    _ensure_path(outpath)
    shell = os.environ.get("COMSPEC", "cmd.exe")
    print(f"Recording active. Type commands below ({STOP_CMD} to stop, {KILL_CMD} to interrupt current command).")

    with open(outpath, "a", encoding="utf-8") as fh:
        while True:
            sys.stdout.write("> ")
            sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                break
            cmd = line.strip()
            _write_event(fh, "in", cmd + "\n")

            if cmd.lower() == STOP_CMD:
                _write_event(fh, "session_end", f"user_command:{STOP_CMD}")
                print("Session stopped.")
                break

            if cmd.lower() == KILL_CMD:
                _kill_current(fh)
                continue

            _run_command(cmd, fh)


# -------------------------
# Cross-platform Entrypoint
# -------------------------
def record(outpath):
    if os.name == "nt":
        record_windows(outpath)
    else:
        record_unix(outpath)
