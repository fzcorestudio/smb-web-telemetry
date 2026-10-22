#!/usr/bin/env python3
"""
FZCORE STUDIO - Multi-Layer Quarantine & Deduplication Engine
Maintains telemetry_data/quarantine_archive.json.
Guarantees that once a lead is processed, emailed, or audited, it is PERMANENTLY
quarantined and NEVER re-scraped, re-audited, or re-emailed.

Multi-Key Deduplication:
1. lead_id
2. domain (e.g. rooftopsolar.us)
3. verified_email (normalized lowercase)
4. composite_key: slugify(business_name) + "::" + slugify(city)
"""

import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "telemetry_data"
QUARANTINE_FILE = DATA_DIR / "quarantine_archive.json"
SENT_LEDGER_FILE = DATA_DIR / "sent_ledger.json"
AUDIT_LEDGER_FILE = DATA_DIR / "audit_ledger.json"

def slugify(text):
    if not text:
        return ""
    text = re.sub(r'[^\w\s-]', '', str(text).lower())
    return re.sub(r'[-\s]+', '-', text).strip()

class QuarantineLedger:
    def __init__(self):
        self.archive = {}
        self.domains = set()
        self.emails = set()
        self.ids = set()
        self.composites = set()
        self.load()

    def load(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if QUARANTINE_FILE.exists():
            try:
                with open(QUARANTINE_FILE, "r", encoding="utf-8") as f:
                    self.archive = json.load(f)
            except Exception:
                self.archive = {}
        else:
            self.archive = {}

        # Auto-seed from sent_ledger if archive is empty or new
        if SENT_LEDGER_FILE.exists():
            try:
                with open(SENT_LEDGER_FILE, "r", encoding="utf-8") as f:
                    sl = json.load(f)
                    for lid, record in sl.items():
                        if lid not in self.archive:
                            self.archive[lid] = {
                                "lead_id": lid,
                                "action": "INITIAL_PITCH_SENT",
                                "quarantined_at": record.get("sent_at", datetime.now(timezone.utc).isoformat()),
                                "domain": record.get("domain", ""),
                                "email": record.get("recipient_email", "").strip().lower(),
                                "business_name": record.get("business_name", ""),
                                "city": record.get("city", ""),
                                "details": record
                            }
            except Exception:
                pass

        self._rebuild_indices()

    def _rebuild_indices(self):
        self.domains.clear()
        self.emails.clear()
        self.ids.clear()
        self.composites.clear()

        for lid, item in self.archive.items():
            self.ids.add(lid)
            d = (item.get("domain") or "").strip().lower()
            if d:
                self.domains.add(d)
            e = (item.get("email") or "").strip().lower()
            if e and "@" in e:
                self.emails.add(e)
            b = item.get("business_name")
            c = item.get("city")
            if b and c:
                self.composites.add(f"{slugify(b)}::{slugify(c)}")

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUARANTINE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.archive, f, indent=2, ensure_ascii=False)

    def is_quarantined(self, lead_id=None, domain=None, email=None, business_name=None, city=None):
        if lead_id and lead_id in self.ids:
            return True, f"Matched lead_id: {lead_id}"

        if domain:
            d_norm = domain.strip().lower()
            if d_norm.startswith("http://"):
                d_norm = d_norm[7:]
            elif d_norm.startswith("https://"):
                d_norm = d_norm[8:]
            d_norm = d_norm.split("/")[0].replace("www.", "")
            if d_norm in self.domains:
                return True, f"Matched domain: {d_norm}"

        if email:
            e_norm = email.strip().lower()
            if e_norm in self.emails:
                return True, f"Matched email: {e_norm}"

        if business_name and city:
            comp = f"{slugify(business_name)}::{slugify(city)}"
            if comp in self.composites:
                return True, f"Matched composite: {comp}"

        return False, "Not quarantined"

    def quarantine_lead(self, lead, action="DISPATCHED", details=None):
        lead_id = lead.get("lead_id") or f"QZ-{int(time.time())}"
        domain = lead.get("domain") or ""
        dm = lead.get("decision_maker", {})
        email = (lead.get("recipient_email") or dm.get("verified_email") or "").strip().lower()
        business_name = lead.get("business_name") or ""
        city = lead.get("city") or ""

        self.archive[lead_id] = {
            "lead_id": lead_id,
            "action": action,
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "domain": domain,
            "email": email,
            "business_name": business_name,
            "city": city,
            "details": details or {}
        }

        # Update fast lookup sets
        self.ids.add(lead_id)
        if domain:
            self.domains.add(domain.lower())
        if email and "@" in email:
            self.emails.add(email.lower())
        if business_name and city:
            self.composites.add(f"{slugify(business_name)}::{slugify(city)}")

        self.save()

    def get_stats(self):
        return {
            "total_quarantined": len(self.archive),
            "unique_domains": len(self.domains),
            "unique_emails": len(self.emails),
            "unique_composites": len(self.composites)
        }

# Global singleton helper
_ledger_instance = None

def get_quarantine_ledger():
    global _ledger_instance
    if _ledger_instance is None:
        _ledger_instance = QuarantineLedger()
    return _ledger_instance

if __name__ == "__main__":
    ql = get_quarantine_ledger()
    print("=" * 65)
    print("🛡️ QUARANTINE LEDGER STATUS")
    print("=" * 65)
    stats = ql.get_stats()
    for k, v in stats.items():
        print(f"• {k.replace('_', ' ').title()}: {v}")
    print("=" * 65)
