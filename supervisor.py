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

def execute_supervised_harvest(duration_seconds=960, max_attempts=15):
    print("=" * 75)
    print("🛡️ [TELEMETRY SUPERVISOR] Initializing Continuous Max-Throttle Scanner")
    print(f"⏱️ Allocated Run Duration: {duration_seconds // 60}m {duration_seconds % 60}s | Zero Lead Cap")
    print("=" * 75)

    from crawler import run_telemetry_harvest

    start_time = time.time()
    current_attempt = 0
    backoff = 4

    while (time.time() - start_time) < duration_seconds and current_attempt < max_attempts:
        try:
            current_attempt += 1
            remaining_time = int(duration_seconds - (time.time() - start_time))
            if remaining_time <= 30:
                print(f"\n⏱️ Cycle time expiring ({remaining_time}s remaining). Finishing cleanly.")
                break

            print(f"\n[Supervisor Session #{current_attempt}] Running continuous crawler ({remaining_time}s remaining in window)...")
            harvested = run_telemetry_harvest(max_duration_seconds=remaining_time)
            
            # If crawler finished normally within time, we're done with the cycle
            if (time.time() - start_time) >= duration_seconds - 30:
                print("\n✅ [Supervisor] Full time-window exhausted with maximum leads yield.")
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
            backoff = min(backoff * 2, 30)

    print("\n🏁 [Supervisor] Max-throttle execution window concluded. Ready for git push.")
    return []

if __name__ == "__main__":
    duration = 960
    args = sys.argv[1:]
    for idx, arg in enumerate(args):
        if arg in ["--duration-minutes", "-d"] and idx + 1 < len(args):
            duration = int(args[idx + 1]) * 60
        elif arg.isdigit():
            duration = int(arg) * 60
    execute_supervised_harvest(duration_seconds=duration)
