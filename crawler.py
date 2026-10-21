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
    "Tax Resolution & CPA Services"
]

TARGET_METROS = [
    {"city": "Dallas", "state": "TX", "country": "US"},
    {"city": "Austin", "state": "TX", "country": "US"},
    {"city": "Houston", "state": "TX", "country": "US"},
    {"city": "Miami", "state": "FL", "country": "US"},
    {"city": "Tampa", "state": "FL", "country": "US"},
    {"city": "Orlando", "state": "FL", "country": "US"},
    {"city": "San Diego", "state": "CA", "country": "US"},
    {"city": "Orange County", "state": "CA", "country": "US"},
    {"city": "Phoenix", "state": "AZ", "country": "US"},
    {"city": "Scottsdale", "state": "AZ", "country": "US"},
    {"city": "Atlanta", "state": "GA", "country": "US"},
    {"city": "Charlotte", "state": "NC", "country": "US"},
    {"city": "Nashville", "state": "TN", "country": "US"},
    {"city": "Denver", "state": "CO", "country": "US"},
    {"city": "London", "state": "Greater London", "country": "UK"},
    {"city": "Manchester", "state": "Greater Manchester", "country": "UK"},
    {"city": "Toronto", "state": "ON", "country": "CA"},
    {"city": "Vancouver", "state": "BC", "country": "CA"},
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

def crawl_regional_telemetry(category, metro, min_rank=20, max_records_per_query=30):
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

            # Deep feed scroll
            feed = page.locator('div[role="feed"]').first
            for _ in range(8):
                try:
                    if feed.count() > 0:
                        feed.evaluate("el => el.scrollBy(0, 4500)")
                    else:
                        page.mouse.wheel(0, 4000)
                except Exception:
                    page.mouse.wheel(0, 4000)
                page.wait_for_timeout(750)

            cards = page.locator("div.Nv2PK").all()
            print(f"[*] Total listings loaded: {len(cards)}")

            target_cards = cards[min_rank:] if len(cards) > min_rank else cards[min(5, len(cards)):]

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
                    seen_domains.add(domain)

                    current_rank = min_rank + idx + 1
                    print(f"🎯 [Rank #{current_rank}] {title} ({review_count} revs, {rating}★) -> {website}")

                    audit = audit_website_telemetry(website)

                    if audit.get("is_online") and audit.get("mx_valid"):
                        owner = audit.get("owner_name", "Business Owner")
                        email = audit.get("verified_email")
                        flaw = audit.get("primary_flaw")
                        price = audit.get("entry_price")

                        snippet = (
                            f"Target: {owner} at {title} ({city}, {state}). "
                            f"Profile: Rank #{current_rank} on Google Maps ({review_count} reviews, {rating}★). "
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
                                "verified_email": email,
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
                        print(f"   ✅ QUALIFIED: {owner} | {flaw} | {price} | MX: {audit['mx_provider']}")

                except Exception:
                    pass

        except Exception as e:
            print(f"❌ Error during crawl: {e}")
        finally:
            browser.close()

    return records

def run_telemetry_harvest(target_count=100, output_file=None):
    print("=" * 75)
    print(f"🚀 [MARKET TELEMETRY] Initializing Regional Scan (Target: {target_count})")
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
        except Exception:
            pass

    niches = list(TARGET_NICHES)
    random.shuffle(niches)
    metros = list(TARGET_METROS)
    random.shuffle(metros)

    new_count = 0
    for metro in metros:
        for niche in niches:
            if new_count >= target_count:
                break

            found = crawl_regional_telemetry(
                category=niche,
                metro=metro,
                min_rank=20,
                max_records_per_query=30
            )

            for item in found:
                if item["domain"] not in existing_domains:
                    all_harvested.append(item)
                    existing_domains.add(item["domain"])
                    new_count += 1
                    print(f"📊 Progress: {new_count} / {target_count} records secured.")

                if new_count >= target_count:
                    break

            # Incremental auto-save
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_harvested, f, indent=2, ensure_ascii=False)

            time.sleep(random.uniform(1.5, 3.0))

        if new_count >= target_count:
            break

    print("\n" + "=" * 75)
    print(f"🎉 Complete! Dataset count: {len(all_harvested)} ({new_count} new)")
    print(f"📁 Saved to: {output_file}")
    print("=" * 75)
    return all_harvested

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_telemetry_harvest(target_count=count)
