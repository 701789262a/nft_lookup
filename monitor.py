import json
import os
import subprocess
import time

import requests
from dotenv import load_dotenv

load_dotenv()

NODE_NAME = os.getenv("NODE_NAME")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
INTERVAL = 10  # seconds


def get_banned_ips() -> list[str]:
    """Run nft command and return the elem list, or empty list if not present."""
    try:
        result = subprocess.run(
            ["nft", "-j", "list", "set", "inet", "pve_smtp_guard", "banned_v4"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"[ERROR] nft command failed: {result.stderr.strip()}")
            return []

        data = json.loads(result.stdout)

        for entry in data.get("nftables", []):
            if "set" in entry:
                return entry["set"].get("elem", [])

    except subprocess.TimeoutExpired:
        print("[ERROR] nft command timed out")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
    except FileNotFoundError:
        print("[ERROR] nft not found — is this running on the right host?")

    return []


def notify_change(added: list[str], removed: list[str]) -> None:
    payload = {
        "node": NODE_NAME,
        "apikey": API_KEY,
        "added": added,
        "removed": removed,
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        print(f"[INFO] Notified API → {resp.status_code}")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to notify API: {e}")


def main():
    print(f"[INFO] Starting monitor (interval={INTERVAL}s, node={NODE_NAME})")
    previous: set[str] = set()
    first_run = True

    while True:
        current_list = get_banned_ips()
        current: set[str] = set(current_list)

        if first_run:
            previous = current
            first_run = False
            print(f"[INFO] Initial snapshot: {len(current)} IPs")
        else:
            added = sorted(current - previous)
            removed = sorted(previous - current)

            if added or removed:
                print(f"[CHANGE] +{len(added)} added, -{len(removed)} removed")
                if added:
                    print(f"  Added:   {added}")
                if removed:
                    print(f"  Removed: {removed}")
                notify_change(added, removed)
            else:
                print(f"[OK] No change ({len(current)} IPs)")

            previous = current

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
