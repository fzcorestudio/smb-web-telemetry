"""
Regional Market Telemetry Crawler (Rank #25 to #200+)
Collects web performance data across regional service providers.
"""

import sys
import os
import json
import time
import random
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auditor import audit_website_telemetry
try:
    from quarantine_manager import get_quarantine_ledger
except ImportError:
    get_quarantine_ledger = None

TARGET_NICHES = [
    "Auto Detailing Ceramic Coating",
    "Paint Protection Film PPF",
    "Mobile Car Wash & Detailing",
    "Window Tinting Commercial & Auto",
    "MedSpa Aesthetics Clinic",
    "Cosmetic Dentistry Veneers",
    "Plastic Surgery Center",
    "Hair Restoration Clinic",
    "Kitchen & Bath Remodeling",
    "Luxury Custom Home Builder",
    "Roofing & Gutter Restoration",
    "Custom Pool & Spa Builder",
    "Hardscaping & Pavers Contractor",
    "Epoxy Flooring & Garage Coating",
    "Commercial HVAC Air Conditioning",
    "Solar Panel Installation",
    "Tree Removal & Arborist Services",
    "Water Damage Restoration & Mold",
    "Foundation Repair & Waterproofing",
    "Custom Fencing & Automatic Gates",
    "Electrician & EV Charger Installation",
    "Plumbing & Sewer Line Replacement",
    "Painting Contractor Interior Exterior",
    "Boutique Branding & Design Agency",
    "Commercial Janitorial & Cleaning",
    "Commercial Pressure Washing",
    "Immigration & Visa Consultant",
    "Tax Resolution & CPA Services",
    "Garage Door Repair & Installation",
    "Concrete Paving & Driveways",
    "Pest Control & Extermination",
    "Commercial Roofing Sheet Metal",
    "Asphalt Paving & Sealcoating",
    "Insulation & Attic Airflow",
    "Glass & Window Replacement",
    "Demolition & Site Excavation",
    "Locksmith & Security Systems",
    "HVAC Duct Cleaning Air Quality"
]

TARGET_METROS = [
    # Texas Triangle & Sub-Metros
    {"city": "Dallas", "state": "TX", "country": "US"},
    {"city": "Plano", "state": "TX", "country": "US"},
    {"city": "Frisco", "state": "TX", "country": "US"},
    {"city": "Arlington", "state": "TX", "country": "US"},
    {"city": "Irving", "state": "TX", "country": "US"},
    {"city": "Fort Worth", "state": "TX", "country": "US"},
    {"city": "Austin", "state": "TX", "country": "US"},
    {"city": "Round Rock", "state": "TX", "country": "US"},
    {"city": "Houston", "state": "TX", "country": "US"},
    {"city": "The Woodlands", "state": "TX", "country": "US"},
    {"city": "Katy", "state": "TX", "country": "US"},
    {"city": "Sugar Land", "state": "TX", "country": "US"},
    {"city": "San Antonio", "state": "TX", "country": "US"},
    # Florida High-Density Hubs
    {"city": "Miami", "state": "FL", "country": "US"},
    {"city": "Fort Lauderdale", "state": "FL", "country": "US"},
    {"city": "Boca Raton", "state": "FL", "country": "US"},
    {"city": "Tampa", "state": "FL", "country": "US"},
    {"city": "St. Petersburg", "state": "FL", "country": "US"},
    {"city": "Clearwater", "state": "FL", "country": "US"},
    {"city": "Orlando", "state": "FL", "country": "US"},
    {"city": "Kissimmee", "state": "FL", "country": "US"},
    {"city": "Jacksonville", "state": "FL", "country": "US"},
    # California & West Coast
    {"city": "San Diego", "state": "CA", "country": "US"},
    {"city": "Orange County", "state": "CA", "country": "US"},
    {"city": "Irvine", "state": "CA", "country": "US"},
    {"city": "Sacramento", "state": "CA", "country": "US"},
    {"city": "San Jose", "state": "CA", "country": "US"},
    # Arizona Desert Hubs
    {"city": "Phoenix", "state": "AZ", "country": "US"},
    {"city": "Scottsdale", "state": "AZ", "country": "US"},
    {"city": "Mesa", "state": "AZ", "country": "US"},
    {"city": "Chandler", "state": "AZ", "country": "US"},
    {"city": "Gilbert", "state": "AZ", "country": "US"},
    {"city": "Tucson", "state": "AZ", "country": "US"},
    # Southeast & East Coast
    {"city": "Atlanta", "state": "GA", "country": "US"},
    {"city": "Marietta", "state": "GA", "country": "US"},
    {"city": "Alpharetta", "state": "GA", "country": "US"},
    {"city": "Charlotte", "state": "NC", "country": "US"},
    {"city": "Raleigh", "state": "NC", "country": "US"},
    {"city": "Durham", "state": "NC", "country": "US"},
    {"city": "Nashville", "state": "TN", "country": "US"},
    {"city": "Franklin", "state": "TN", "country": "US"},
    {"city": "Memphis", "state": "TN", "country": "US"},
    # Mountain & Midwest
    {"city": "Denver", "state": "CO", "country": "US"},
    {"city": "Aurora", "state": "CO", "country": "US"},
    {"city": "Colorado Springs", "state": "CO", "country": "US"},
    {"city": "Salt Lake City", "state": "UT", "country": "US"},
    {"city": "Las Vegas", "state": "NV", "country": "US"},
    {"city": "Henderson", "state": "NV", "country": "US"},
    {"city": "Kansas City", "state": "MO", "country": "US"},
    {"city": "Overland Park", "state": "KS", "country": "US"},
    {"city": "Indianapolis", "state": "IN", "country": "US"},
    {"city": "Columbus", "state": "OH", "country": "US"},
    {"city": "Cincinnati", "state": "OH", "country": "US"},
    {"city": "Cleveland", "state": "OH", "country": "US"},
    {"city": "Pittsburgh", "state": "PA", "country": "US"},
    # Pacific Northwest
    {"city": "Portland", "state": "OR", "country": "US"},
    {"city": "Seattle", "state": "WA", "country": "US"},
    {"city": "Bellevue", "state": "WA", "country": "US"},
    {"city": "Tacoma", "state": "WA", "country": "US"},
    {"city": "Oklahoma City", "state": "OK", "country": "US"},
    {"city": "Richmond", "state": "VA", "country": "US"},
    # International Commonwealth Strongholds
    {"city": "London", "state": "Greater London", "country": "UK"},
    {"city": "Manchester", "state": "Greater Manchester", "country": "UK"},
    {"city": "Birmingham", "state": "West Midlands", "country": "UK"},
    {"city": "Leeds", "state": "West Yorkshire", "country": "UK"},
    {"city": "Toronto", "state": "ON", "country": "CA"},
    {"city": "Vancouver", "state": "BC", "country": "CA"},
    {"city": "Calgary", "state": "AB", "country": "CA"},
    {"city": "Sydney", "state": "NSW", "country": "AU"},
    {"city": "Melbourne", "state": "VIC", "country": "AU"},
    {"city": "Brisbane", "state": "QLD", "country": "AU"}
]

EXCLUDED_DOMAINS = [
    "google.", "gstatic.", "yelp.", "facebook.", "instagram.", "yellowpages.",
    "mapquest.", "tripadvisor.", "linkedin.", "bbb.org", "wikipedia.",
    "angieslist.", "thumbtack.", "threebestrated.", "topdetailers.",
    "preferredmechanic.", "expertise.", "houzz.", "superpages.", "crunchbase.",
    "glassdoor.", "pinterest.", "twitter.", "x.com", "youtube.", "tiktok.",
    "groupon.", "wix.", "squarespace.", "apple.", "microsoft.", "amazon.",
    "forbes.", "homedepot.", "lowes.", "angi.com", "bark.com"
]

def crawl_regional_telemetry(category, metro, min_rank=0, max_records_per_query=30, existing_domains=None, quarantine_ledger=None):
    from playwright.sync_api import sync_playwright

    city = metro["city"]
    state = metro["state"]
    country = metro["country"]
    query = f"{category} in {city} {state}"

    print(f"\n[Telemetry Crawler] Scanning '{query}' (Rank #{min_rank}+)...")
    records = []
    seen_domains = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            extra_http_headers={
                "Cookie": "CONSENT=YES+cb.20230531-04-p0.en+FX+417; SOCS=CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwNjE4LjA2X3AwGgJlbiACGgYIgLCzpAY;"
            }
        )
        page = context.new_page()

        maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}?hl=en"
        try:
            page.goto(maps_url, timeout=35000)
            page.wait_for_timeout(2000)

            # Dismiss Google Consent Dialog
            for consent_btn in page.locator('button:has-text("Accept all"), button:has-text("I agree"), form[action*="consent"] button').all():
                try:
                    if consent_btn.is_visible():
                        consent_btn.click()
                        page.wait_for_timeout(1000)
                        break
                except Exception:
                    pass

            # Deep adaptive feed scroll (reaches full Google Maps limit ~120 cards)
            feed = page.locator('div[role="feed"]').first
            prev_card_count = 0
            stagnant_count = 0

            for scroll_idx in range(1, 26):
                try:
                    if feed.count() > 0:
                        feed.evaluate("el => el.scrollBy(0, 10000)")
                    else:
                        page.mouse.wheel(0, 10000)
                except Exception:
                    page.mouse.wheel(0, 10000)
                page.wait_for_timeout(800)

                current_card_count = page.locator("div.Nv2PK").count()

                # Check if bottom of Google Maps index reached
                if page.locator("text=\"You've reached the end of the list\"").count() > 0:
                    break

                if current_card_count == prev_card_count:
                    stagnant_count += 1
                    if stagnant_count >= 2:
                        break
                else:
                    stagnant_count = 0
                prev_card_count = current_card_count

            cards = page.locator("div.Nv2PK").all()
            print(f"[*] Total listings loaded: {len(cards)} (Zero Rank Skipping: Evaluating from Rank #1 to #{len(cards)})")

            # Zero Rank Skipping: inspect every single card from Rank #1
            target_cards = cards[min_rank:] if min_rank > 0 else cards

            for idx, card in enumerate(target_cards):
                if len(records) >= max_records_per_query:
                    break

                try:
                    title_el = card.locator(".qBF1Pd").first
                    if title_el.count() == 0:
                        continue
                    title = title_el.inner_text().strip()

                    rating = 0.0
                    review_count = 0
                    rate_el = card.locator("span.MW4etd").first
                    if rate_el.count() > 0:
                        try:
                            rating = float(rate_el.inner_text().strip())
                        except Exception:
                            pass

                    rev_el = card.locator("span.UY7F9").first
                    if rev_el.count() > 0:
                        try:
                            rev_str = rev_el.inner_text().strip().replace("(", "").replace(")", "").replace(",", "")
                            review_count = int(rev_str)
                        except Exception:
                            pass

                    # Strictly 3 to 28 reviews (hungry SMBs)
                    if review_count < 3 or review_count > 28:
                        continue

                    website = None
                    for a in card.locator("a").all():
                        href = (a.get_attribute("href") or "").strip()
                        if not href or href.startswith("/aclk") or "google.com" in href:
                            continue
                        website = href.split("?")[0].rstrip("/")
                        break

                    if not website:
                        continue

                    domain = urllib.parse.urlparse(website).netloc.lower().replace("www.", "")
                    if domain in seen_domains or any(bad in domain for bad in EXCLUDED_DOMAINS):
                        continue

                    # Instant Early Deduplication (Skip known/quarantined in 0.001s without HTTP/DNS load)
                    if existing_domains and domain in existing_domains:
                        continue
                    if quarantine_ledger:
                        is_q, q_reason = quarantine_ledger.is_quarantined(
                            domain=domain,
                            business_name=title,
                            city=city
                        )
                        if is_q:
                            continue

                    seen_domains.add(domain)
                    if existing_domains is not None:
                        existing_domains.add(domain)

                    current_rank = (min_rank or 0) + idx + 1
                    print(f"🎯 [Rank #{current_rank}] {title} ({review_count} revs, {rating}★) -> {website}")

                    audit = audit_website_telemetry(website)

                    if audit.get("is_online") and audit.get("mx_valid"):
                        owner = audit.get("owner_name", "Business Owner")
                        first_name = audit.get("first_name")
                        email = audit.get("verified_email")
                        flaw = audit.get("primary_flaw")
                        price = audit.get("entry_price")
                        tier_label = audit.get("tier_label", "TIER_5_GENERIC")
                        tier_level = audit.get("tier_level", 5)

                        snippet = (
                            f"Target: {owner} at {title} ({city}, {state}). "
                            f"Profile: Rank #{current_rank} on Google Maps ({review_count} reviews, {rating}★). "
                            f"Decision Maker: {tier_label} (Priority {tier_level}). "
                            f"Audit Flaw: {audit['concrete_flaw_details']} "
                            f"Pitch Offer: {audit['matched_service']} for {price} ({audit['turnaround']} turnaround). "
                            f"Deliverability: MX verified via {audit['mx_provider']}."
                        )

                        record = {
                            "lead_id": f"FZ-{country}-{int(time.time())}-{len(records)+1}",
                            "estimated_rank": current_rank,
                            "business_name": title,
                            "category": category,
                            "city": city,
                            "state": state,
                            "country": country,
                            "website": website,
                            "domain": domain,
                            "reviews_count": review_count,
                            "rating": rating,
                            "decision_maker": {
                                "name": owner,
                                "first_name": first_name,
                                "title": "Owner / Founder" if tier_level in [1, 4] else "Decision Maker",
                                "verified_email": email,
                                "tier": tier_label,
                                "tier_level": tier_level,
                                "email_status": "MX_DELIVERABLE_0_BOUNCE" if email else "DOMAIN_MX_VERIFIED",
                                "mx_provider": audit["mx_provider"]
                            },
                            "audit_diagnostics": {
                                "primary_flaw": flaw,
                                "concrete_observation": audit["concrete_flaw_details"],
                                "matched_fzcore_service": audit["matched_service"],
                                "recommended_entry_price": price,
                                "turnaround": audit["turnaround"]
                            },
                            "gemini_context_snippet": snippet,
                            "harvested_at": datetime.now(timezone.utc).isoformat()
                        }

                        records.append(record)
                        print(f"   ✅ QUALIFIED [P{tier_level}: {tier_label}]: {owner} <{email}> | {flaw} | {price}")

                except Exception:
                    pass

        except Exception as e:
            print(f"❌ Error during crawl: {e}")
        finally:
            browser.close()

    return records

def run_telemetry_harvest(max_duration_seconds=960, target_count=None, output_file=None):
    start_time = time.time()
    print("=" * 75)
    print(f"🚀 [MAXIMUM-THROTTLE HARVESTER] Continuous Time-Window Mode Active")
    print(f"⏱️ Maximum Cycle Runtime: {max_duration_seconds // 60}m {max_duration_seconds % 60}s (No numeric lead cap)")
    print("=" * 75)

    if not output_file:
        output_file = BASE_DIR / "telemetry_data" / "market_records.json"
    else:
        output_file = Path(output_file)

    all_harvested = []
    existing_domains = set()

    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
                if isinstance(prev_data, list):
                    all_harvested = prev_data
                    existing_domains = {l.get("domain") for l in all_harvested if l.get("domain")}
                    print(f"ℹ️ Loaded {len(all_harvested)} baseline records from existing dataset.")
        except Exception:
            pass

    state_file = output_file.parent / "crawler_state.json"
    metro_cursor = 0
    niche_cursor = 0
    total_queries_run = 0

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                metro_cursor = state_data.get("metro_cursor", 0)
                niche_cursor = state_data.get("niche_cursor", 0)
                total_queries_run = state_data.get("total_queries_run", 0)
                print(f"📍 Resuming Crawler from Cursor: Metro #{metro_cursor % len(TARGET_METROS)} ({TARGET_METROS[metro_cursor % len(TARGET_METROS)]['city']}) | Niche #{niche_cursor % len(TARGET_NICHES)} ({TARGET_NICHES[niche_cursor % len(TARGET_NICHES)]})")
        except Exception:
            pass

    ql = get_quarantine_ledger() if get_quarantine_ledger else None
    new_count = 0
    queries_this_run = 0

    num_metros = len(TARGET_METROS)
    num_niches = len(TARGET_NICHES)

    print(f"\n🔄 --- Beginning Interleaved Round-Robin Sweep ({num_metros} Metros × {num_niches} Niches) ---")

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_duration_seconds:
            print(f"\n⏱️ Time window complete ({int(elapsed)}s elapsed). Closing cycle...")
            break

        if target_count and new_count >= target_count:
            break

        metro = TARGET_METROS[metro_cursor % num_metros]
        niche = TARGET_NICHES[niche_cursor % num_niches]

        found = crawl_regional_telemetry(
            category=niche,
            metro=metro,
            min_rank=0,
            max_records_per_query=30,
            existing_domains=existing_domains,
            quarantine_ledger=ql
        )

        for item in found:
            d = item.get("domain", "")
            all_harvested.append(item)
            existing_domains.add(d)
            new_count += 1
            time_left = max(0, int(max_duration_seconds - (time.time() - start_time)))
            print(f"📊 Progress: {new_count} new leads secured | {len(all_harvested)} total | {time_left}s remaining in cycle.")

        # Real-time incremental save
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_harvested, f, indent=2, ensure_ascii=False)

        # Update cursor (Interleaved: advance metro every query, and niche every query)
        metro_cursor = (metro_cursor + 1) % num_metros
        niche_cursor = (niche_cursor + 1) % num_niches
        total_queries_run += 1
        queries_this_run += 1

        # Persist cursor state
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "metro_cursor": metro_cursor,
                    "niche_cursor": niche_cursor,
                    "total_queries_run": total_queries_run,
                    "last_metro": metro["city"],
                    "last_niche": niche,
                    "last_harvest_at": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception:
            pass

        if target_count and new_count >= target_count:
            break

        time.sleep(random.uniform(1.0, 2.0))

    total_time = int(time.time() - start_time)
    print("\n" + "=" * 75)
    print(f"🎉 Cycle Complete in {total_time}s! Total in dataset: {len(all_harvested)} ({new_count} new this run)")
    print(f"📁 Leads Saved to: {output_file}")
    print("=" * 75)
    return all_harvested

if __name__ == "__main__":
    duration = 960
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        duration = int(sys.argv[1]) * 60
    run_telemetry_harvest(max_duration_seconds=duration)
