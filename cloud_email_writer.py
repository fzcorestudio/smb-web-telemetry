#!/usr/bin/env python3
"""
FZCORE STUDIO - Autonomous Cloud Email Writing Engine
Runs in GitHub Actions Cloud at 02:30 PM PKT right after the Deep Forensic Lead Audit.
- Ingests telemetry_data/vetted_master_dossier.json.
- Selects from 4 Battle-Tested Copywriting Angles based on 12-dimension DOM flaws.
- Strictly enforces ZERO em-dashes ('—' or '--') and zero robotic AI buzzwords.
- Chris Voss "No-Oriented" CTAs: Low-friction 20-second screen preview.
- Generates telemetry_data/approved_pitches.json & telemetry_data/pitch_review_dashboard.html.
- Execution speed: ~2-3 seconds for 100 leads (pure in-memory NLP & angle matching).
"""

import sys
import os
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "telemetry_data"

VETTED_DOSSIER_FILE = DATA_DIR / "vetted_master_dossier.json"
APPROVED_PITCHES_FILE = DATA_DIR / "approved_pitches.json"
DASHBOARD_FILE = DATA_DIR / "pitch_review_dashboard.html"

BANNED_AI_TOKENS = [
    "—", "--", "elevate", "delve", "seamless", "revolutionize",
    "cutting-edge", "game-changer", "testament", "tapestry",
    "furthermore", "moreover", "in today's digital landscape",
    "i hope this email finds you well", "synergy", "paradigm",
    "innovative", "streamline", "beacon", "foster", "unlock"
]

def clean_human_text(text):
    """Enforces strict anti-AI rules: replaces em-dashes while preserving clean paragraph line breaks."""
    t = text.replace("—", ", ").replace("--", ", ")
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in t.splitlines()]
    cleaned = re.sub(r'\n{3,}', '\n\n', "\n".join(lines)).strip()
    return cleaned

def craft_super_personalized_pitch(lead):
    b_name = lead.get("business_name", "Business").strip()
    city = lead.get("city", "").strip()
    state = lead.get("state", "").strip()
    category = lead.get("category", "Local Service").strip()
    domain = lead.get("domain", "").strip()
    reviews = lead.get("reviews_count", 15)
    rating = lead.get("rating", 5.0)

    dm = lead.get("decision_maker", {})
    name = dm.get("name", "").strip()
    first_name = dm.get("first_name")
    stop_words = {"business", "owner", "admin", "info", "contact", "support", "of", "the", "company", "team", "sales", "office", "general", "manager"}
    if first_name and first_name.lower() in stop_words:
        first_name = None

    if not first_name and name:
        cands = [w for w in name.split() if w.lower() not in stop_words and len(w) >= 2]
        if cands:
            first_name = cands[0].capitalize()

    greeting = f"Hi {first_name}," if first_name else "Hi there,"
    subj_owner_suffix = f"for {first_name} re {domain}" if first_name else f"about {domain}"

    fa = lead.get("forensic_audit", {})
    flaws = fa.get("flaws_inventory", [])
    primary_leak = fa.get("primary_money_leak", "")
    est_loss = fa.get("estimated_monthly_loss") or lead.get("vibe_audit", {}).get("estimated_monthly_loss", "$4,000/mo")

    flaw_ids = [f.get("flaw_id") for f in flaws]

    has_call_leak = any(x in flaw_ids for x in ["NO_TAP_TO_CALL_LINK", "MISSING_PHONE_ABOVE_FOLD", "MISSING_STICKY_BOTTOM_BAR"])
    has_form_leak = any(x in flaw_ids for x in ["HIGH_FRICTION_STATIC_FORM", "MISSING_INSTANT_ESTIMATOR"])
    has_viewport_leak = "MOBILE_VIEWPORT_OVERFLOW" in flaw_ids
    has_redesign_leak = any(x in flaw_ids for x in ["OUTDATED_COPYRIGHT_ERA", "LEGACY_TABLE_LAYOUT"]) or "Redesign" in lead.get("vibe_audit", {}).get("bleed_type", "")

    # Angle Matching Matrix
    if has_viewport_leak:
        subject = f"quick note {subj_owner_suffix}" if first_name else f"{domain} mobile layout issue"
        body = (
            f"{greeting}\n\n"
            f"Was looking at your {category.lower()} work in {city}. Great track record with your {reviews} Google reviews.\n\n"
            f"Pulled up {domain} on my iPhone and noticed the layout overflows horizontally off the edge of the screen, "
            f"which makes the screen slide sideways and cuts off your contact buttons on phones.\n\n"
            f"I put together a quick viewport patch for {b_name} that locks the layout tight and makes everything crisp on iPhone and Android. "
            f"Would it be a bad idea if I sent over a quick 20-second screen recording showing the fix?\n\n"
            f"Best,\nFaiz Majeed\nFZCORE Studio"
        )
        angle_name = "Mobile Viewport Un-Breaking"

    elif has_call_leak:
        subject = f"quick question {subj_owner_suffix}" if first_name else f"{domain} mobile call button"
        body = (
            f"{greeting}\n\n"
            f"Came across your {category.lower()} work in {city}. Solid reputation with your {reviews} reviews on Google.\n\n"
            f"Pulled up your site on my iPhone this morning and noticed the phone number isn't 1-tap clickable, and when you scroll down to check your past projects, the contact option disappears off the screen. "
            f"Most homeowners shopping on mobile want to call with one tap; when they have to memorize or copy-paste digits, a lot of them just tap back to the next contractor on Google Maps.\n\n"
            f"I mocked up a fast, brand-matched tap-to-call bar and sticky quote button for {b_name} on mobile. "
            f"Would you be opposed to me sending over a short 20-second screen demo? (No pitch or pressure either way).\n\n"
            f"Best,\nFaiz Majeed\nFZCORE Studio"
        )
        angle_name = "1-Tap Call & Sticky Bottom Bar"

    elif has_form_leak:
        subject = f"{domain} quick estimate calculator"
        body = (
            f"{greeting}\n\n"
            f"Was checking out your {category.lower()} projects in {city}, your portfolio looks great.\n\n"
            f"Looked at your site on mobile and noticed there's a static contact form with no quick pricing guide, so visitors have to wait for a manual callback. "
            f"In {category.lower()}, most homeowners want a fast ballpark in under a minute; otherwise they usually submit quote requests on 3 competitor sites instead.\n\n"
            f"I put together an interactive 60-second instant project estimator built specifically for {b_name} that lets mobile visitors get a ballpark range and texts you their project details instantly. "
            f"Mind if I send over a 20-second preview link to see how it looks?\n\n"
            f"Best,\nFaiz Majeed\nFZCORE Studio"
        )
        angle_name = "60-Second Instant Quote Estimator"

    elif has_redesign_leak:
        subject = f"quick question {subj_owner_suffix}"
        body = (
            f"{greeting}\n\n"
            f"Came across your work in {city}. Really solid track record with your {reviews} reviews on Google.\n\n"
            f"I noticed on mobile that your site is still running on an older layout with an older copyright. "
            f"High-end clients looking for {category.lower()} usually judge credibility within 5 seconds on their phone before deciding whether to call.\n\n"
            f"I mocked up a clean, modern executive preview for {b_name} that showcases your work much sharper on iPhone. "
            f"Would you be open to seeing a 20-second preview? (Zero pitch or pressure either way).\n\n"
            f"Best,\nFaiz Majeed\nFZCORE Studio"
        )
        angle_name = "Modern Bento Credibility Revamp"

    else:
        subject = f"quick note {subj_owner_suffix}"
        body = (
            f"{greeting}\n\n"
            f"Was looking over your {category.lower()} projects in {city}. Great reputation with your {reviews} reviews on Google.\n\n"
            f"Looked at your site on mobile and noticed there's no sticky tap-to-call bar when scrolling, so mobile visitors have to scroll back up or zoom in to reach you. "
            f"A lot of homeowners looking for quick estimates end up tapping the next contractor on Google Maps when that happens.\n\n"
            f"I put together a clean mobile call bar and instant quote estimator preview for {b_name}. "
            f"Would you be opposed to me sending over a short 20-second screen demo? (Zero pitch or pressure either way).\n\n"
            f"Best,\nFaiz Majeed\nFZCORE Studio"
        )
        angle_name = "Mobile Friction Reduction"

    clean_subj = clean_human_text(subject)
    clean_body = clean_human_text(body)

    for bad in BANNED_AI_TOKENS:
        if bad in clean_subj.lower() or bad in clean_body.lower():
            raise ValueError(f"AI Cliché / Em-Dash '{bad}' detected in pitch for {b_name}!")

    return clean_subj, clean_body, angle_name, est_loss

def build_review_dashboard_html(pitches):
    cards_html = []

    for idx, p in enumerate(pitches, 1):
        lead = p["lead"]
        b_name = lead.get("business_name")
        city = lead.get("city")
        state = lead.get("state")
        cat = lead.get("category")
        site = lead.get("website")
        email = p.get("recipient_email") or "Domain Inbox"
        reviews = lead.get("reviews_count", 0)
        rating = lead.get("rating", 5.0)
        rank = lead.get("estimated_rank", "N/A")
        tier_label = lead.get("decision_maker", {}).get("tier", "TIER_5_GENERIC")

        maps_q = urllib.parse.quote_plus(f"{b_name} {city} {state}")
        maps_url = f"https://www.google.com/maps/search/?api=1&query={maps_q}"

        subj = p["subject"]
        body = p["body"]

        subj_enc = urllib.parse.quote_plus(subj)
        body_enc = urllib.parse.quote_plus(body)
        mailto_url = f"mailto:{email}?subject={subj_enc}&body={body_enc}"

        fa = lead.get("forensic_audit", {})
        flaws = fa.get("flaws_inventory", [])
        evidence_pills = []
        for f in flaws[:2]:
            evidence_pills.append(f"<span class='evidence-pill' title='{f.get('client_money_impact')}'>🔍 {f.get('flaw_title')}</span>")
        evidence_html = "".join(evidence_pills) if evidence_pills else f"<span class='evidence-pill'>⚠️ {p['bleed_type']}</span>"

        card = f"""
        <div class="pitch-card" id="card-{idx}">
            <div class="card-header">
                <div class="header-left">
                    <span class="idx-badge">#{idx}</span>
                    <h2 class="biz-title">{b_name}</h2>
                    <span class="cat-chip">{cat}</span>
                    <span class="loc-chip">📍 {city}, {state}</span>
                </div>
                <div class="header-right">
                    <a href="{maps_url}" target="_blank" class="maps-pill" title="Verify reviews on Google Maps">
                        ★ {rating:.1f} ({reviews} reviews) • Rank #{rank} ↗
                    </a>
                    <a href="{site}" target="_blank" class="site-pill" title="Open live website">
                        🌐 {lead.get('domain')} ↗
                    </a>
                </div>
            </div>

            <div class="email-meta-bar">
                <div class="meta-item">
                    <strong>To:</strong> 
                    <span class="email-to">{email}</span> 
                    <span class="tier-badge">{tier_label}</span>
                </div>
                <div class="meta-item">
                    <strong>Angle:</strong> <span class="angle-badge">{p['angle']}</span>
                </div>
                <div class="meta-item subject-row">
                    <strong>Subject:</strong> <span class="email-subj">{subj}</span>
                </div>
            </div>

            <div class="flaws-bar">
                {evidence_html}
                <span class="loss-badge">💸 Revenue Bleed: {p['estimated_loss']}</span>
            </div>

            <div class="pitch-body-box">
                <pre id="body-text-{idx}">{body}</pre>
            </div>

            <div class="card-footer">
                <button class="copy-btn" onclick="copyPitch({idx})">
                    📋 Copy Email
                </button>
                <a href="{mailto_url}" class="send-btn">
                    ✉ 1-Click Send via Mail Client
                </a>
            </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FZCORE Studio • Super-Personalized Email Review Dashboard</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0b0f19;
        color: #f1f5f9;
        padding: 30px 20px;
        line-height: 1.5;
    }}
    .container {{
        max-width: 1040px;
        margin: 0 auto;
    }}
    .dashboard-header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        padding: 24px 30px;
        border-radius: 14px;
        margin-bottom: 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .brand-title {{
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
    }}
    .brand-sub {{
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }}
    .header-badges {{
        display: flex;
        gap: 12px;
    }}
    .stat-badge {{
        background: #0f172a;
        border: 1px solid #38bdf8;
        padding: 8px 16px;
        border-radius: 8px;
        text-align: right;
    }}
    .stat-num {{
        font-size: 20px;
        font-weight: 800;
        color: #38bdf8;
    }}
    .stat-lbl {{
        font-size: 10px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .rule-pill {{
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        display: flex;
        align-items: center;
    }}
    .pitch-card {{
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .pitch-card:hover {{
        border-color: #38bdf8;
    }}
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
        gap: 16px;
    }}
    .header-left {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .idx-badge {{
        background: #1e293b;
        color: #94a3b8;
        font-weight: 800;
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 6px;
    }}
    .biz-title {{
        font-size: 19px;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.3px;
    }}
    .cat-chip {{
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
    }}
    .loc-chip {{
        background: #1e293b;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 500;
        padding: 3px 8px;
        border-radius: 6px;
    }}
    .header-right {{
        display: flex;
        gap: 8px;
        flex-shrink: 0;
    }}
    .maps-pill, .site-pill {{
        text-decoration: none;
        font-size: 11px;
        font-weight: 600;
        padding: 5px 10px;
        border-radius: 6px;
        transition: opacity 0.15s;
    }}
    .maps-pill {{
        background: rgba(234, 179, 8, 0.12);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.25);
    }}
    .site-pill {{
        background: #1e293b;
        color: #cbd5e1;
        border: 1px solid #334155;
    }}
    .maps-pill:hover, .site-pill:hover {{
        opacity: 0.8;
    }}
    .email-meta-bar {{
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 12px;
        font-size: 13px;
    }}
    .meta-item {{
        margin-bottom: 6px;
    }}
    .meta-item:last-child {{
        margin-bottom: 0;
    }}
    .email-to {{
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
    }}
    .tier-badge {{
        background: rgba(147, 51, 234, 0.18);
        color: #c084fc;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
    }}
    .angle-badge {{
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .email-subj {{
        color: #f1f5f9;
        font-weight: 700;
    }}
    .flaws-bar {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: center;
        margin-bottom: 14px;
    }}
    .evidence-pill {{
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 5px;
    }}
    .loss-badge {{
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.25);
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 5px;
    }}
    .pitch-body-box {{
        background: #090d16;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    pre {{
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        font-size: 14px;
        color: #e2e8f0;
        white-space: pre-wrap;
        line-height: 1.6;
    }}
    .card-footer {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 12px;
    }}
    .copy-btn {{
        background: #1e293b;
        color: #f1f5f9;
        border: 1px solid #334155;
        padding: 9px 16px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: background 0.15s;
    }}
    .copy-btn:hover {{
        background: #334155;
    }}
    .send-btn {{
        background: #0284c7;
        color: #ffffff;
        text-decoration: none;
        padding: 9px 18px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        transition: background 0.15s;
    }}
    .send-btn:hover {{
        background: #0369a1;
    }}
</style>
<script>
    function copyPitch(idx) {{
        const text = document.getElementById('body-text-' + idx).innerText;
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.querySelector('#card-' + idx + ' .copy-btn');
            const orig = btn.innerText;
            btn.innerText = '✅ Copied!';
            btn.style.borderColor = '#22c55e';
            setTimeout(() => {{
                btn.innerText = orig;
                btn.style.borderColor = '#334155';
            }}, 2000);
        }});
    }}
</script>
</head>
<body>
<div class="container">
    <div class="dashboard-header">
        <div>
            <h1 class="brand-title">FZCORE Studio • Cloud Email Engine</h1>
            <p class="brand-sub">Pattern-Interrupt Founder Cold Outbound • 100% Human Direct-Response</p>
        </div>
        <div class="header-badges">
            <div class="rule-pill">🛡️ 0 Em-Dashes • Zero AI Slop</div>
            <div class="stat-badge">
                <div class="stat-num">{len(pitches)}</div>
                <div class="stat-lbl">Ready Pitches</div>
            </div>
        </div>
    </div>

    {cards_joined}
</div>
</body>
</html>
"""
    return html

def run_cloud_email_writer():
    print("=" * 70)
    print("✍️ [CLOUD EMAIL ENGINE] Crafting Super-Personalized Human Pitches")
    print("🚫 Strict Rules: ZERO Em-Dashes ('—'), Zero Buzzwords, Chris Voss CTAs")
    print("=" * 70)

    start_time = datetime.now()

    leads = []
    if VETTED_DOSSIER_FILE.exists():
        try:
            leads = json.load(open(VETTED_DOSSIER_FILE, "r", encoding="utf-8"))
        except Exception:
            pass

    print(f"📦 Qualified Forensic Leads Ingested: {len(leads)}")

    approved_pitches = []

    for i, lead in enumerate(leads, 1):
        b_name = lead.get("business_name", "Unknown")
        email = lead.get("decision_maker", {}).get("verified_email")

        try:
            subj, body, angle, loss = craft_super_personalized_pitch(lead)

            approved_pitches.append({
                "lead_id": lead.get("lead_id"),
                "business_name": b_name,
                "recipient_email": email,
                "recipient_name": lead.get("decision_maker", {}).get("name", "Business Owner"),
                "category": lead.get("category"),
                "city": lead.get("city"),
                "state": lead.get("state"),
                "website": lead.get("website"),
                "subject": subj,
                "body": body,
                "angle": angle,
                "bleed_type": lead.get("forensic_audit", {}).get("primary_money_leak") or lead.get("vibe_audit", {}).get("bleed_type", "Mobile Conversion Leak"),
                "estimated_loss": loss,
                "lead": lead
            })

            print(f"[{i}/{len(leads)}] Generated Pitch for: {b_name} [{angle}]")

        except Exception as e:
            print(f"⚠️ Error crafting pitch for {b_name}: {e}")

    # Save approved pitches JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(APPROVED_PITCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(approved_pitches, f, indent=2, ensure_ascii=False)

    # Build and save HTML review dashboard
    dashboard_html = build_review_dashboard_html(approved_pitches)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(dashboard_html)

    elapsed = (datetime.now() - start_time).total_seconds()
    print("=" * 70)
    print(f"✅ Cloud Email Generation Complete: {len(approved_pitches)} Pitches in {elapsed:.2f}s!")
    print(f"📁 JSON File: {APPROVED_PITCHES_FILE}")
    print(f"💻 Interactive Dashboard: {DASHBOARD_FILE}")
    print("=" * 70 + "\n")

    return approved_pitches

if __name__ == "__main__":
    run_cloud_email_writer()
