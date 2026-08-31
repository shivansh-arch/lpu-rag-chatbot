# open_debug_chrome.py

import subprocess
import time
import requests

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PROFILE_DIR = r"C:\temp\chrome-debug-profile"
DEBUG_PORT = 9222

def main():
    try:
        requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1)
        print("Chrome is already open with the debug port active. Nothing to do.")
        return
    except requests.exceptions.ConnectionError:
        pass

    print("Launching Chrome with remote debugging enabled...")
    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={DEBUG_PROFILE_DIR}",
    ])

    for _ in range(20):
        try:
            requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1)
            print("Chrome is up and the debug port is reachable.")
            print("Now log into UMS manually in the window that opened.")
            return
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    raise RuntimeError(
        "Chrome didn't start with the debug port open in time. "
        "Check for leftover chrome.exe processes and try again."
    )

if __name__ == "__main__":
    main()