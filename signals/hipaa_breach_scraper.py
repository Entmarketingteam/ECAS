import csv
import io
import re
import urllib.request
import urllib.parse
import http.cookiejar
from datetime import datetime
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
from tools.seen_tracker import SeenTracker
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

# The portal is a server-rendered JSF app, NOT a JSON API. The data lives behind
# a stateful CSV export on breach_report_hip.jsf (the "Cases Under Investigation"
# view — HHS only lists breaches affecting 500+ individuals). The old code hit an
# invented activecases.json that 404s, so it always returned [].
BREACH_PORTAL_URL = "https://ocrportal.hhs.gov/ocr/breach/breach_report_hip.jsf"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def parse_breach_csv(csv_text: str) -> list[dict]:
    """Parse the HHS breach CSV positionally.

    Row 0 is PrimeFaces UIPanel junk, not usable headers, so DictReader would
    mismatch — index by column position instead:
    0=Covered Entity, 1=State, 3=Individuals Affected, 4=Submission Date,
    5=Type of Breach.
    """
    if not csv_text.strip():
        return []
    rows = list(csv.reader(io.StringIO(csv_text)))
    if len(rows) < 2:
        return []
    out = []
    for rec in rows[1:]:
        if len(rec) < 6:
            continue
        company = rec[0].strip()
        if not company:
            continue
        out.append({
            "company_name": company,
            "state": rec[1].strip(),
            "breach_type": rec[5].strip(),
            "individuals_affected": rec[3].strip(),
            "breach_date": rec[4].strip(),
        })
    return out


def select_recent_breaches(cases: list[dict], max_n: int) -> list[dict]:
    """Return the freshest max_n breaches by submission date.

    The portal lists ~728 breaches (24-month window); routing all of them on the
    first run would flood warmup-sensitive sending infra. Cap to the most recent
    so the source drips freshest-first (dedup carries the rest to later runs).
    """
    def key(c):
        try:
            return datetime.strptime(c.get("breach_date", ""), "%m/%d/%Y")
        except ValueError:
            return datetime.min  # bad/blank dates sort last
    return sorted(cases, key=key, reverse=True)[:max_n]


def extract_export_form(html: str) -> dict:
    """Pull the runtime JSF values needed to POST the CSV export.

    The CSV button id (e.g. ocrForm:j_idt385) is an auto-generated Mojarra id
    that shifts whenever HHS redeploys the page; hardcoding it yields a silent
    200-with-HTML failure. Read it (and the ViewState) from the page each run.
    """
    vs = re.search(r'javax\.faces\.ViewState[^>]*?value="([^"]+)"', html)
    if not vs:
        vs = re.search(r'name="javax\.faces\.ViewState"[^>]*?value="([^"]+)"', html)
    viewstate = vs.group(1) if vs else None

    # The CSV export is a Mojarra command link, not the <img>. The <img id> sitting
    # ON csv.png (e.g. ocrForm:j_idt385) is NOT a JSF command source — posting it is
    # silently ignored and returns 200+HTML. The real source is in the enclosing
    # <a onclick="mojarra.jsfcljs(form,{'ocrForm:j_idtNNN':'...'},'')">, and its number
    # is one less than the img id (and the whole block shifts on every redeploy). Walk
    # back from the csv <img> to its anchor and pull the source id from the jsfcljs map.
    csv_button_id = None
    mimg = re.search(r"<img[^>]*csv\.png", html)
    if mimg:
        a_start = html.rfind("<a ", 0, mimg.start())
        if a_start != -1:
            onclick = html[a_start:mimg.start()]
            cmd = re.search(r"jsfcljs\([^,]*,\s*\{'(ocrForm:j_idt\d+)'", onclick)
            if cmd:
                csv_button_id = cmd.group(1)
    return {"viewstate": viewstate, "csv_button_id": csv_button_id}


def fetch_active_hipaa_breaches() -> list[dict]:
    """Fetch HHS OCR breaches currently under investigation via the portal's own
    CSV export. Two-request stateful flow over plain urllib (no browser):
    GET seeds the session cookie + ViewState, POST triggers the CSV download."""
    print("=== Fetching HHS OCR Active HIPAA Breaches ===")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", _UA), ("Accept", "text/html,*/*")]
    try:
        with opener.open(BREACH_PORTAL_URL, timeout=30) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
        form = extract_export_form(page)
        if not form["viewstate"] or not form["csv_button_id"]:
            print(f"  [Error] Could not extract export form ids: {form}")
            return []

        # Minimal verified body: form marker + the CSV command source + ViewState is
        # all JSF needs to stream the CSV (tested live — the other ocrForm hidden
        # fields are not required, and replaying them would just reintroduce the
        # j_idt id-shift fragility this extractor exists to avoid).
        body = urllib.parse.urlencode({
            "ocrForm": "ocrForm",
            form["csv_button_id"]: form["csv_button_id"],
            "javax.faces.ViewState": form["viewstate"],
        }).encode("utf-8")
        req = urllib.request.Request(BREACH_PORTAL_URL, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Referer", BREACH_PORTAL_URL)
        with opener.open(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "")
            data = resp.read().decode("utf-8", errors="ignore")
        # Sanity: a stale button id returns 200 + HTML, not CSV. Fail loud-ish.
        if "csv" not in ctype.lower() and "text/html" in ctype.lower():
            print(f"  [Error] Export returned HTML not CSV (button id likely shifted): {ctype}")
            return []
        cases = parse_breach_csv(data)
        print(f"  Retrieved {len(cases)} breach records")
        return cases
    except Exception as e:
        print(f"  [Error] HHS HIPAA Breach portal export failed: {e}")
        return []


def run_hipaa_outbound_pipeline(max_per_run: int = 50):
    """Process HHS active breaches, extract decision makers (Compliance, IT, COOs),
    verify, route to Smartlead. Dedups on entity+date so the same months-long
    investigation is not re-routed every run, and caps to the freshest
    max_per_run breaches so the first run does not flood sending infra."""
    cases = fetch_active_hipaa_breaches()
    if not cases:
        return

    cases = select_recent_breaches(cases, max_per_run)
    seen = SeenTracker("hipaa_leads_seen")

    for case in cases:
        company_name = case["company_name"]
        dedup_key = f"hipaa::{company_name}::{case['breach_date']}"
        if seen.is_seen(dedup_key):
            continue

        print(f"Processing HIPAA Breach: {company_name} | State: {case['state']} | Affected: {case['individuals_affected']}")

        # Only target companies large enough for a real compliance crisis.
        try:
            if int(str(case["individuals_affected"]).replace(",", "")) < 500:
                print("  [Filtered] Breach affected less than 500 individuals. Skipping.")
                seen.mark_seen(dedup_key)
                continue
        except ValueError:
            pass

        domain = resolve_domain(company_name)
        if not domain:
            sync_dead_letter_queue_to_airtable(case, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            seen.mark_seen(dedup_key)
            continue

        target_titles = ["Chief Compliance Officer", "Compliance Director", "IT Director", "COO", "General Counsel"]
        contacts = find_contacts_for_domain(domain, target_titles)
        if not contacts:
            sync_dead_letter_queue_to_airtable({"company_name": company_name, "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            seen.mark_seen(dedup_key)
            continue

        for c in contacts:
            email = c.get("email")
            status, source = verify_email_cascade(email)

            c["verification_status"] = status
            c["source"] = source
            c["sector"] = "Document Destruction & HIPAA Compliance"
            c["custom_fields"] = {
                "breach_type": case["breach_type"],
                "affected_individuals": str(case["individuals_affected"]),
                "breach_date": case["breach_date"],
            }

            if status in ["verified_clean", "catch_all_verified"]:
                print(f"  [Success] routing {email} ({status}) under breach audit to Smartlead")
                route_lead_to_n8n(c)
            else:
                sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

        seen.mark_seen(dedup_key)


if __name__ == "__main__":
    run_hipaa_outbound_pipeline()
