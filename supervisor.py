"""
Autonomous Process Supervisor & Self-Healing Watchguard
Ensures high-availability telemetry crawling with process cleanup.
"""

import sys
import os
import time
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "telemetry_data"
LOG_FILE = DATA_DIR / "supervisor_events.log"

def cleanup_zombie_processes():
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["taskkill", "/f", "/im", "chromium.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["pkill", "-9", "-f", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def log_event(attempt, error_str, tb_str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write(f"TIMESTAMP: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"ATTEMPT: #{attempt}\n")
        f.write(f"ERROR: {error_str}\n")
        f.write("TRACE:\n")
        f.write(tb_str)
        f.write("\n" + "=" * 70 + "\n")

def execute_supervised_harvest(target_records=50, max_attempts=10):
    print("=" * 75)
    print("🛡️ [TELEMETRY SUPERVISOR] Initializing High-Availability Scanner")
    print(f"🎯 Target Records: {target_records} | Max Recovery Cycles: {max_attempts}")
    print("=" * 75)

    from crawler import run_telemetry_harvest

    current_attempt = 0
    backoff = 5

    while current_attempt < max_attempts:
        try:
            current_attempt += 1
            print(f"\n[Supervisor Session #{current_attempt}] Running crawler...")
            harvested = run_telemetry_harvest(target_count=target_records)
            
            if len(harvested) >= target_records:
                print(f"\n✅ [Supervisor] Target of {target_records} records fulfilled.")
                return harvested
            else:
                return harvested

        except KeyboardInterrupt:
            print("\n🛑 Manual interrupt received. Stopping cleanly.")
            sys.exit(0)

        except Exception as e:
            err = str(e)
            tb = traceback.format_exc()
            print(f"\n⚠️ [Supervisor Recovery] Exception on attempt #{current_attempt}: {err}")
            cleanup_zombie_processes()
            log_event(current_attempt, err, tb)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)

    return []

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    execute_supervised_harvest(target_records=count)
