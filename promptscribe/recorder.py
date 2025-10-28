# promptscribe/recorder.py
import os
import sys
import time
import json
import subprocess
import threading
import queue

def _write_event(fh, kind, data):
    evt = {"ts": time.time(), "kind": kind, "data": data}
    fh.write(json.dumps(evt, ensure_ascii=False) + "\n")
    fh.flush()


# -------------------------
# Unix PTY backend
# -------------------------
def record_unix(outpath):
    import pty, select

    master, slave = pty.openpty()
    pid = os.fork()
    if pid == 0:
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        shell = os.environ.get("SHELL", "/bin/bash")
        os.execvp(shell, [shell])
    else:
        with open(outpath, "a", encoding="utf-8") as fh:
            try:
                while True:
                    r, _, _ = select.select([master], [], [])
                    if master in r:
                        data = os.read(master, 4096)
                        if not data:
                            break
                        text = data.decode("utf-8", errors="replace")
                        _write_event(fh, "out", text)
                        os.write(1, data)
            except KeyboardInterrupt:
                pass


# -------------------------
# Windows subprocess backend (thread-safe)
# -------------------------
def record_windows(outpath):
    shell = os.environ.get("COMSPEC", "cmd.exe")

    process = subprocess.Popen(
        shell,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    output_queue = queue.Queue()
    input_queue = queue.Queue()
    stop_flag = threading.Event()

    # --- Reader thread for stdout ---
    def reader():
        for line in iter(process.stdout.readline, ""):
            output_queue.put(line)
        stop_flag.set()

    # --- Reader thread for stdin ---
    def input_reader():
        while not stop_flag.is_set():
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                input_queue.put(line)
            except Exception:
                break

    threading.Thread(target=reader, daemon=True).start()
    threading.Thread(target=input_reader, daemon=True).start()

    print("Recording active. Type commands below (type 'exit' to stop):")

    with open(outpath, "a", encoding="utf-8") as fh:
        try:
            while not stop_flag.is_set():
                # Handle user input
                while not input_queue.empty():
                    cmd = input_queue.get()
                    _write_event(fh, "in", cmd)
                    if cmd.strip().lower() == "exit":
                        process.stdin.write(cmd + "\n")
                        process.stdin.flush()
                        stop_flag.set()
                        raise KeyboardInterrupt
                    process.stdin.write(cmd)
                    process.stdin.flush()

                # Handle process output
                while not output_queue.empty():
                    line = output_queue.get()
                    _write_event(fh, "out", line)
                    sys.stdout.write(line)
                    sys.stdout.flush()

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\nRecording stopped.")
        finally:
            try:
                stop_flag.set()
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                pass


# -------------------------
# Cross-platform entrypoint
# -------------------------
def record(outpath):
    if os.name == "nt":
        record_windows(outpath)
    else:
        record_unix(outpath)
