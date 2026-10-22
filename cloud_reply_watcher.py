#!/usr/bin/env python3
"""
FZCORE STUDIO - Autonomous IMAP Reply Detection Engine (SSL Port 993)
Monitors Hostinger inboxes for prospect replies.
When a prospect replies to an outreach thread:
1. Immediately marks the lead as 'REPLIED' in followup_pipeline.json.
2. PERMANENTLY CLEARS any scheduled follow-ups (auto-stop sequence).
3. Adds to telemetry_data/replies_inbox.json with snippet and timestamp.
4. Quarantines lead in quarantine_archive.json under 'CLIENT_REPLIED'.
"""

import sys
import os
import re
import json
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("SUBDOMAIN_MAIL_PASS"):
        load_dotenv(Path(__file__).resolve().parent.parent / "fzcore_web" / ".env")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "telemetry_data"
MAILBOXES_FILE = BASE_DIR / "mailboxes.json"
FOLLOWUP_FILE = DATA_DIR / "followup_pipeline.json"
REPLIES_FILE = DATA_DIR / "replies_inbox.json"
SENT_LEDGER_FILE = DATA_DIR / "sent_ledger.json"

try:
    from quarantine_manager import get_quarantine_ledger
except ImportError:
    get_quarantine_ledger = None

IMAP_HOST = "imap.hostinger.com"
IMAP_PORT = 993

def clean_header_text(header_val):
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                result.append(part.decode("latin-1", errors="ignore"))
        else:
            result.append(str(part))
    return "".join(result).strip()

def extract_email_address(raw_str):
    if not raw_str:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+', raw_str)
    return match.group(0).lower() if match else ""

def get_body_snippet(msg):
    snippet = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    payload = part.get_payload(decode=True)
                    if payload:
                        snippet = payload.decode('utf-8', errors='ignore')
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                snippet = payload.decode('utf-8', errors='ignore')
    except Exception:
        pass
    clean = re.sub(r'\s+', ' ', snippet).strip()
    return clean[:300]

def check_for_lead_replies():
    password = os.getenv("SUBDOMAIN_MAIL_PASS")
    if not password:
        print("⚠️ [IMAP Reply Watcher] Missing SUBDOMAIN_MAIL_PASS. Skipping reply scan.")
        return 0

    if not MAILBOXES_FILE.exists():
        print(f"⚠️ Mailboxes config missing: {MAILBOXES_FILE}")
        return 0

    with open(MAILBOXES_FILE, "r", encoding="utf-8") as f:
        mailboxes = json.load(f)

    # Load follow-up pipeline
    pipeline = {}
    if FOLLOWUP_FILE.exists():
        try:
            with open(FOLLOWUP_FILE, "r", encoding="utf-8") as f:
                pipeline = json.load(f)
        except Exception:
            pipeline = {}

    # Load replies archive
    replies_archive = []
    if REPLIES_FILE.exists():
        try:
            with open(REPLIES_FILE, "r", encoding="utf-8") as f:
                replies_archive = json.load(f)
        except Exception:
            replies_archive = []

    # Map prospect emails to pipeline keys
    prospect_map = {}
    for lid, entry in pipeline.items():
        if entry.get("status") != "REPLIED":
            rec_email = (entry.get("recipient_email") or "").strip().lower()
            if rec_email:
                prospect_map[rec_email] = lid

    # Also map from sent_ledger if not in pipeline
    if SENT_LEDGER_FILE.exists():
        try:
            with open(SENT_LEDGER_FILE, "r", encoding="utf-8") as f:
                sl = json.load(f)
                for lid, sent_item in sl.items():
                    rec_email = (sent_item.get("recipient_email") or "").strip().lower()
                    if rec_email and rec_email not in prospect_map:
                        if lid not in pipeline or pipeline[lid].get("status") != "REPLIED":
                            prospect_map[rec_email] = lid
        except Exception:
            pass

    if not prospect_map:
        print("ℹ️ [IMAP Reply Watcher] Zero active un-replied prospects in pipeline. Inboxes are clear.")
        return 0

    print("=" * 75)
    print("📬 [IMAP REPLY WATCHER] Scanning Hostinger Mailboxes for Prospect Responses...")
    print(f"🎯 Actively Monitored Prospects: {len(prospect_map)} Waiting Leads")
    print("=" * 75)

    # Determine which sender inboxes actually dispatched emails to check
    sender_inboxes = set()
    for lid, entry in pipeline.items():
        s_email = entry.get("sender_email")
        if s_email:
            sender_inboxes.add(s_email)
    if SENT_LEDGER_FILE.exists():
        try:
            with open(SENT_LEDGER_FILE, "r", encoding="utf-8") as f:
                sl = json.load(f)
                for sent_item in sl.values():
                    s_email = sent_item.get("sender_email")
                    if s_email:
                        sender_inboxes.add(s_email)
        except Exception:
            pass

    # If sender_inboxes is empty, scan first 5 mailboxes as fallback
    if not sender_inboxes:
        sender_inboxes = {m["user"] for m in mailboxes[:5]}

    ql = get_quarantine_ledger() if get_quarantine_ledger else None
    new_replies_found = 0

    for sender_user in sorted(sender_inboxes):
        try:
            client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=12)
            client.login(sender_user, password)
            client.select("INBOX", readonly=True)

            # Search recent unread or all messages from past 7 days
            status, data = client.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                client.logout()
                continue

            msg_ids = data[0].split()
            # Inspect last 30 messages in this inbox
            recent_ids = msg_ids[-30:] if len(msg_ids) > 30 else msg_ids

            for mid in reversed(recent_ids):
                r_status, msg_data = client.fetch(mid, "(RFC822.HEADER)")
                if r_status != "OK" or not msg_data:
                    continue

                raw_email = msg_data[0][1]
                parsed_msg = email.message_from_bytes(raw_email)

                sender_header = clean_header_text(parsed_msg.get("From"))
                sender_email = extract_email_address(sender_header)
                subject = clean_header_text(parsed_msg.get("Subject"))
                in_reply_to = clean_header_text(parsed_msg.get("In-Reply-To"))

                # Check match against active prospects
                matched_lid = prospect_map.get(sender_email)
                if matched_lid:
                    # Fetch full body snippet
                    b_status, full_data = client.fetch(mid, "(RFC822)")
                    full_parsed = email.message_from_bytes(full_data[0][1]) if b_status == "OK" else parsed_msg
                    snippet = get_body_snippet(full_parsed)

                    print(f"\n🚨 [CLIENT REPLY DETECTED] From: {sender_header} <{sender_email}>")
                    print(f"   Subject: {subject}")
                    print(f"   Snippet: {snippet[:120]}...")
                    print(f"   🛑 AUTO-STOP: Freezing follow-ups for lead {matched_lid} permanently!")

                    # Update followup pipeline
                    if matched_lid in pipeline:
                        pipeline[matched_lid]["status"] = "REPLIED"
                        pipeline[matched_lid]["replied_at"] = datetime.now(timezone.utc).isoformat()
                        pipeline[matched_lid]["reply_snippet"] = snippet
                        pipeline[matched_lid]["next_followup_due"] = None
                    else:
                        pipeline[matched_lid] = {
                            "lead_id": matched_lid,
                            "recipient_email": sender_email,
                            "status": "REPLIED",
                            "replied_at": datetime.now(timezone.utc).isoformat(),
                            "reply_snippet": snippet,
                            "next_followup_due": None
                        }

                    # Add to replies archive
                    reply_entry = {
                        "lead_id": matched_lid,
                        "prospect_email": sender_email,
                        "sender_header": sender_header,
                        "mailbox_received": sender_user,
                        "subject": subject,
                        "snippet": snippet,
                        "received_at": datetime.now(timezone.utc).isoformat()
                    }
                    replies_archive.append(reply_entry)

                    # Quarantine permanently
                    if ql:
                        ql.quarantine_lead(
                            lead={"lead_id": matched_lid, "recipient_email": sender_email},
                            action="CLIENT_REPLIED",
                            details=reply_entry
                        )

                    # Remove from prospect map so we don't duplicate
                    del prospect_map[sender_email]
                    new_replies_found += 1

            client.logout()

        except Exception as e:
            # Individual mailbox timeout/auth error handled gracefully
            continue

    # Save updated pipeline and replies archive
    if new_replies_found > 0:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(FOLLOWUP_FILE, "w", encoding="utf-8") as f:
            json.dump(pipeline, f, indent=2, ensure_ascii=False)
        with open(REPLIES_FILE, "w", encoding="utf-8") as f:
            json.dump(replies_archive, f, indent=2, ensure_ascii=False)

    print(f"\n🏁 IMAP Scan Complete. New Replies Detected & Sequences Halted: {new_replies_found}")
    print("=" * 75 + "\n")
    return new_replies_found

if __name__ == "__main__":
    check_for_lead_replies()
