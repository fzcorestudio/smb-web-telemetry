"""
Autonomous Process Supervisor & Self-Healing Watchguard
Manages the Daily 3-Stage Recurring Pipeline (Pakistan Standard Time / PKT):
Stage 1: 12:00 AM - 12:00 PM PKT -> Continuous Harvester & MX Handshake
Stage 2: 12:00 PM - 02:30 PM PKT -> 100-Lead/Cycle Cloud Deep Auditor & Owner Hunter
Stage 3: 02:30 PM - 03:00 PM PKT -> Cloud Email Writing Engine & Review Dashboard
Stage 4: Outside Hours           -> Incremental Deep Auditor or On-Demand Harvest
"""

import sys
import os
import json
import time
import subprocess
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

def get_current_pkt_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=5)

def run_supervisor_pipeline(duration_seconds=960, force_mode=None):
    pkt_now = get_current_pkt_time()
    pkt_time_str = pkt_now.strftime("%I:%M %p PKT")
    pkt_hour = pkt_now.hour
    pkt_minute = pkt_now.minute

    print("=" * 75)
    print(f"🛡️ [SUPERVISOR] Pakistan Standard Time: {pkt_time_str} (UTC+5)")
    print("=" * 75)

    # Determine Active Mode:
    # Mode A: Harvest Window (12:00 AM PKT to 12:00 PM PKT)
    # Mode B: Deep Audit Window (12:00 PM PKT to 2:30 PM PKT)
    # Mode C: Email Writing Window (02:30 PM PKT to 03:00 PM PKT)
    # Mode D: Outside hours -> Check if leads need auditing, otherwise harvest
    if force_mode:
        active_mode = force_mode.upper()
    elif 0 <= pkt_hour < 12:
        active_mode = "HARVEST"
    elif 12 <= pkt_hour < 14 or (pkt_hour == 14 and pkt_minute <= 30):
        active_mode = "AUDIT"
    elif pkt_hour == 14 and pkt_minute > 30:
        active_mode = "WRITE_PITCHES"
    else:
        # Check if we have unaudited leads in market_records
        market_file = DATA_DIR / "market_records.json"
        ledger_file = DATA_DIR / "audit_ledger.json"
        has_unaudited = False
        if market_file.exists():
            try:
                records = json.load(open(market_file, encoding='utf-8'))
                ledger = set(json.load(open(ledger_file, encoding='utf-8'))) if ledger_file.exists() else set()
                pending = [r for r in records if r.get('lead_id') not in ledger and r.get('decision_maker', {}).get('verified_email')]
                if len(pending) > 0:
                    has_unaudited = True
            except Exception:
                pass
        active_mode = "AUDIT" if has_unaudited else "HARVEST"

    print(f"📍 Active Scheduled Pipeline Stage: [{active_mode}]")
    print("=" * 75 + "\n")

    if active_mode == "WRITE_PITCHES":
        print("✍️ [STAGE 3] Running Autonomous Cloud Email Writer (Super-Personalized Pitches)...")
        from cloud_email_writer import run_cloud_email_writer
        try:
            run_cloud_email_writer()
        except Exception as e:
            log_event(1, str(e), traceback.format_exc())
            print(f"⚠️ Email Writer exception logged: {e}")

    elif active_mode == "AUDIT":
        print("🔍 [STAGE 2] Running Autonomous Cloud Deep Auditor (100 Leads / Cycle)...")
        from cloud_deep_auditor import run_cloud_deep_audit
        try:
            run_cloud_deep_audit(batch_size=100)
            print("\n✍️ [STAGE 3] Auto-Chaining Cloud Email Writer for Vetted Leads...")
            from cloud_email_writer import run_cloud_email_writer
            run_cloud_email_writer()
        except Exception as e:
            cleanup_zombie_processes()
            log_event(1, str(e), traceback.format_exc())
            print(f"⚠️ Audit exception logged: {e}")
    else:
        print("🌙 [STAGE 1] Running Overnight Continuous Harvester (Google Maps Rank #25 to #200+)...")
        from crawler import run_telemetry_harvest
        try:
            run_telemetry_harvest(max_duration_seconds=duration_seconds)
        except Exception as e:
            cleanup_zombie_processes()
            log_event(1, str(e), traceback.format_exc())
            print(f"⚠️ Harvest exception logged: {e}")

    print("\n🏁 [Supervisor] Cycle concluded cleanly. Ready for Git Auto-Commit.")

if __name__ == "__main__":
    force_mode = None
    duration = 960  # Default 16 minutes
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ["--mode", "-m"] and i + 1 < len(args):
            force_mode = args[i + 1]
        elif a in ["--duration-minutes", "-d"] and i + 1 < len(args):
            duration = int(args[i + 1]) * 60
        elif a.isdigit():
            duration = int(a) * 60
    run_supervisor_pipeline(duration_seconds=duration, force_mode=force_mode)
