import os
import sys
import subprocess
import threading
import signal
import time

shell = os.environ.get("SHELL", "/bin/bash")

proc = subprocess.Popen(
    [shell],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    preexec_fn=os.setsid
)

command_running = False

# prevent syscalls from breaking on SIGINT
signal.siginterrupt(signal.SIGINT, False)


def reader():
    global command_running

    while True:
        line = proc.stdout.readline()

        if not line:
            break

        clean = line.rstrip()

        # command start marker
        if clean == "__CMD_START__":
            command_running = True
            continue

        # command end marker
        if clean.startswith("__CMD_END__"):
            command_running = False

            exit_code = clean.replace("__CMD_END__", "").strip()

            print(f"\n[command exited with code {exit_code}]")
            continue

        print(line, end="", flush=True)


threading.Thread(target=reader, daemon=True).start()

print("Persistent shell test started.")
print("Type 'exit' to quit.")

while True:
    try:
        # shell exited
        if proc.poll() is not None:
            print("Shell process exited.")
            break

        # avoid busy loop
        if command_running:
            time.sleep(0.05)
            continue

        # prompt
        sys.stdout.write("> ")
        sys.stdout.flush()

        cmd = sys.stdin.readline()

        if not cmd:
            break

        cmd = cmd.strip()

        # exit shell
        if cmd == "exit":
            try:
                proc.stdin.write("exit\n")
                proc.stdin.flush()
            except BrokenPipeError:
                pass

            break

        # wrap command with markers
        wrapped = (
            'echo "__CMD_START__"\n'
            f'{cmd}\n'
            'echo "__CMD_END__$?"\n'
        )

        proc.stdin.write(wrapped)
        proc.stdin.flush()

    except KeyboardInterrupt:
        # interrupt currently running command
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)

                print("\n[Interrupted current command]")

                # clear terminal input buffer
                try:
                    import termios
                    termios.tcflush(sys.stdin, termios.TCIFLUSH)
                except Exception:
                    pass

            except ProcessLookupError:
                break

            continue

    except BrokenPipeError:
        print("Shell pipe closed.")
        break

print("Session ended.")