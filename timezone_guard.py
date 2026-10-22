#!/usr/bin/env python3
"""
FZCORE STUDIO - Autonomous Working Hours & Timezone Engine
Ensures cold outreach and follow-ups are dispatched STRICTLY within the prospect's
local business working hours (Monday-Friday, 08:30 AM to 05:00 PM local time).
Supports US States, Canadian Provinces, Australian States, and UK.
"""

import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

STATE_TIMEZONE_MAP = {
    # United States - Eastern Time
    "CT": "America/New_York", "DE": "America/New_York", "FL": "America/New_York",
    "GA": "America/New_York", "IN": "America/Indiana/Indianapolis", "KY": "America/New_York",
    "ME": "America/New_York", "MD": "America/New_York", "MA": "America/New_York",
    "MI": "America/Detroit", "NH": "America/New_York", "NJ": "America/New_York",
    "NY": "America/New_York", "NC": "America/New_York", "OH": "America/New_York",
    "PA": "America/New_York", "RI": "America/New_York", "SC": "America/New_York",
    "TN": "America/New_York", "VT": "America/New_York", "VA": "America/New_York",
    "WV": "America/New_York", "DC": "America/New_York",

    # United States - Central Time
    "AL": "America/Chicago", "AR": "America/Chicago", "IL": "America/Chicago",
    "IA": "America/Chicago", "KS": "America/Chicago", "LA": "America/Chicago",
    "MN": "America/Chicago", "MS": "America/Chicago", "MO": "America/Chicago",
    "NE": "America/Chicago", "ND": "America/Chicago", "OK": "America/Chicago",
    "SD": "America/Chicago", "TX": "America/Chicago", "WI": "America/Chicago",

    # United States - Mountain Time
    "AZ": "America/Phoenix",  # Arizona does not observe DST
    "CO": "America/Denver", "ID": "America/Boise", "MT": "America/Denver",
    "NM": "America/Denver", "UT": "America/Denver", "WY": "America/Denver",

    # United States - Pacific Time
    "CA": "America/Los_Angeles", "NV": "America/Los_Angeles",
    "OR": "America/Los_Angeles", "WA": "America/Los_Angeles",

    # Canada
    "ON": "America/Toronto", "QC": "America/Montreal", "BC": "America/Vancouver",
    "AB": "America/Edmonton", "MB": "America/Winnipeg", "NS": "America/Halifax",

    # Australia
    "NSW": "Australia/Sydney", "VIC": "Australia/Melbourne", "QLD": "Australia/Brisbane",
    "WA_AU": "Australia/Perth", "SA": "Australia/Adelaide",

    # United Kingdom
    "UK": "Europe/London", "GB": "Europe/London"
}

def resolve_timezone(state=None, country=None):
    if state:
        s_clean = state.strip().upper()
        if s_clean in STATE_TIMEZONE_MAP:
            return STATE_TIMEZONE_MAP[s_clean]
    if country:
        c_clean = country.strip().upper()
        if c_clean in ["UK", "GB", "UNITED KINGDOM"]:
            return "Europe/London"
        if c_clean in ["AU", "AUSTRALIA"]:
            return "Australia/Sydney"
        if c_clean in ["CA", "CANADA"]:
            return "America/Toronto"
    # Default to US Eastern Time (dominant contractor market)
    return "America/New_York"

def get_prospect_local_time(state=None, country=None):
    tz_str = resolve_timezone(state, country)
    return datetime.now(ZoneInfo(tz_str)), tz_str

def is_prospect_working_hours(state=None, country=None, allow_weekends=False):
    """
    Returns True if current local time at the prospect's location is:
    - Monday through Friday (unless allow_weekends=True)
    - Between 08:30 AM (8.5) and 05:00 PM (17.0) local time.
    """
    local_dt, tz_str = get_prospect_local_time(state, country)

    # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
    if not allow_weekends and local_dt.weekday() >= 5:
        return False, f"Weekend ({local_dt.strftime('%A')}) in {tz_str}"

    decimal_hour = local_dt.hour + (local_dt.minute / 60.0)
    if 8.5 <= decimal_hour <= 17.0:
        return True, f"Working Hours ({local_dt.strftime('%I:%M %p %Z')})"
    else:
        return False, f"Outside Working Hours ({local_dt.strftime('%I:%M %p %Z')})"

if __name__ == "__main__":
    test_locs = [("AZ", "US"), ("NY", "US"), ("CA", "US"), ("ON", "CA"), ("NSW", "AU")]
    print("=" * 65)
    print("🕒 PROSPECT LOCAL WORKING HOURS STATUS VERIFICATION")
    print("=" * 65)
    for s, c in test_locs:
        ok, reason = is_prospect_working_hours(s, c)
        dt, tz = get_prospect_local_time(s, c)
        status_icon = "🟢 ACTIVE WINDOW" if ok else "⏸️ INACTIVE WINDOW"
        print(f"[{s}, {c}] -> {status_icon}: {reason}")
    print("=" * 65)
