import subprocess
import re
import time
import os
import signal
import sys

TUNNEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tunnel_url")
CLOUDFLARED_BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "cloudflared")

running_proc = None

def cleanup(sig=None, frame=None):
    global running_proc
    if running_proc:
        try:
            running_proc.terminate()
            running_proc.wait(timeout=2)
        except Exception:
            running_proc.kill()
    if os.path.exists(TUNNEL_FILE):
        try:
            os.remove(TUNNEL_FILE)
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_tunnel():
    global running_proc
    while True:
        print("[TunnelManager] Launching Cloudflare quick tunnel to http://localhost:8501...")
        running_proc = subprocess.Popen(
            [CLOUDFLARED_BIN, "tunnel", "--url", "http://localhost:8501"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        url = None
        while running_proc.poll() is None:
            line = running_proc.stderr.readline()
            if not line:
                time.sleep(0.1)
                continue
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                url = m.group(0)
                print(f"[TunnelManager] Active Tunnel URL: {url}")
                with open(TUNNEL_FILE, "w") as f:
                    f.write(url.strip())
                break

        # Wait for process to exit or monitor
        running_proc.wait()
        print("[TunnelManager] Cloudflare tunnel exited. Reconnecting in 3s...")
        time.sleep(3)

if __name__ == "__main__":
    run_tunnel()
