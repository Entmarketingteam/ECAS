#!/usr/bin/env python3
"""
Scan all Smartlead campaigns for mojibake (UTF-8 bytes mis-decoded as Latin-1/CP1252).
Run with --fix to repair in place.

    python3 tools/smartlead_mojibake_audit.py          # report
    python3 tools/smartlead_mojibake_audit.py --fix    # report + repair
"""
import json, os, re, sys, subprocess, urllib.request, urllib.error

API_KEY = os.environ.get("SMARTLEAD_API_KEY") or subprocess.check_output(
    ["doppler","secrets","get","SMARTLEAD_API_KEY","--project","ent-agency-automation","--config","dev","--plain"]
).decode().strip()
BASE = "https://server.smartlead.ai/api/v1"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

# Signatures of UTF-8 -> Latin1/CP1252 mis-decode. â€ alone catches “ ” — ' '.
MOJIBAKE = re.compile(r"â€|Â |Ã©|Ã¨|Ã ")


def get(path):
    req = urllib.request.Request(f"{BASE}{path}{'&' if '?' in path else '?'}api_key={API_KEY}", headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def post(path, body):
    req = urllib.request.Request(
        f"{BASE}{path}{'&' if '?' in path else '?'}api_key={API_KEY}",
        data=json.dumps(body).encode("utf-8"), headers=UA, method="POST",
    )
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:300]}"


def repair(s):
    if not s or not MOJIBAKE.search(s): return s
    for enc in ("latin-1", "cp1252"):
        try: return s.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError): continue
    return s


def main():
    fix = "--fix" in sys.argv
    campaigns = get("/campaigns")
    bad = []
    for c in campaigns:
        cid = c["id"]
        seqs = get(f"/campaigns/{cid}/sequences")
        if not isinstance(seqs, list): continue
        hits, payload = [], []
        for s in seqs:
            variants = s.get("seq_variants")
            delay = (s.get("seq_delay_details") or {})
            delay_days = delay.get("delay_in_days") or delay.get("delayInDays") or 0
            if variants:
                new_v = []
                for v in variants:
                    nsubj, nbody = repair(v.get("subject") or ""), repair(v.get("email_body") or "")
                    if nsubj != (v.get("subject") or "") or nbody != (v.get("email_body") or ""):
                        hits.append((s.get("seq_number"), v.get("variant_label")))
                    new_v.append({
                        "id": v.get("id"), "subject": nsubj, "email_body": nbody,
                        "variant_label": v.get("variant_label"),
                        "variant_distribution_percentage": v.get("variant_distribution_percentage"),
                    })
                payload.append({
                    "id": s.get("id"), "seq_number": s.get("seq_number"),
                    "seq_delay_details": {"delay_in_days": delay_days},
                    "variant_distribution_type": s.get("variant_distribution_type"),
                    "lifetime_volume": s.get("lifetime_volume"),
                    "per_day_volume": s.get("per_day_volume"),
                    "distribute_lead_across_test_variants": s.get("distribute_lead_across_test_variants"),
                    "winning_metric_property": s.get("winning_metric_property"),
                    "seq_variants": new_v,
                })
            else:
                nsubj, nbody = repair(s.get("subject") or ""), repair(s.get("email_body") or "")
                if nsubj != (s.get("subject") or "") or nbody != (s.get("email_body") or ""):
                    hits.append((s.get("seq_number"), "main"))
                payload.append({
                    "id": s.get("id"), "seq_number": s.get("seq_number"),
                    "seq_delay_details": {"delay_in_days": delay_days},
                    "subject": nsubj, "email_body": nbody,
                })
        if hits:
            bad.append((cid, c.get("name",""), hits))
            print(f"[BAD] {cid} {c.get('name','')[:60]}  -> {hits}")
            if fix:
                print("       ", post(f"/campaigns/{cid}/sequences", {"sequences": payload})[:120])
    if not bad:
        print("All campaigns clean.")
    sys.exit(1 if (bad and not fix) else 0)


if __name__ == "__main__":
    main()
