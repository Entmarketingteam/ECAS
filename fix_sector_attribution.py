#!/usr/bin/env python3
"""
Fix sector attribution for unrouted ECAS contacts.
Steps:
  1. Fetch contacts without smartlead_campaign_id
  2. Resolve sector via linked project → positioning_notes JSON
  3. Fallback: keyword match on company name
  4. Update analyst_notes in Airtable for resolved contacts
"""
import os, requests, json, re, time
from collections import Counter

AT_KEY = os.environ['AIRTABLE_API_KEY']
BASE_ID = 'appoi8SzEJY8in57x'
CONTACTS_TABLE = 'tblPBvTBuhwlS8AnS'
PROJECTS_TABLE = 'tbloen0rEkHttejnC'
AT_HEADERS = {'Authorization': f'Bearer {AT_KEY}', 'Content-Type': 'application/json'}

CAMPAIGN_MAP = {
    'Power & Grid Infrastructure': 3005694,
    'Defense': None,
    'Industrial & Manufacturing Facilities': 3040601,
    'Data Center & AI Infrastructure': 3040599,
    'Water & Wastewater': 3040600,
    'Nuclear & Critical Minerals': None,
}

COMPANY_SECTOR_KEYWORDS = {
    'Power & Grid Infrastructure': ['electric', 'power', 'grid', 'energy', 'utility', 'transmission',
                                     'substation', 'voltage', 'solar', 'wind', 'renewable', 'lineman',
                                     'wiring', 'cable', 'conductor', 'switchgear', 'transformer'],
    'Defense': ['defense', 'federal', 'military', 'government', 'aerospace', 'dod', 'navfac',
                'army', 'navy', 'marine', 'air force', 'pentagon', 'lockheed', 'raytheon',
                'northrop', 'general dynamics', 'l3', 'bae'],
    'Data Center & AI Infrastructure': ['data center', 'datacenter', 'cloud', 'colocation', 'hyperscale',
                                          'equinix', 'digital realty', 'coresite', 'ntt', 'server',
                                          'computing', 'ai infrastructure'],
    'Industrial & Manufacturing Facilities': ['industrial', 'manufacturing', 'chemical', 'process',
                                               'pharma', 'pharmaceutical', 'plant', 'facility',
                                               'fabrication', 'production', 'factory'],
    'Water & Wastewater': ['water', 'wastewater', 'municipal', 'treatment', 'sewer', 'stormwater',
                            'desalin', 'irrigation', 'pipeline', 'aqua'],
}


def fetch_all(table_id):
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset
        r = requests.get(f'https://api.airtable.com/v0/{BASE_ID}/{table_id}',
                         headers={'Authorization': f'Bearer {AT_KEY}'}, params=params)
        data = r.json()
        if 'error' in data:
            print(f'  Airtable error: {data}')
            break
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break
    return records


def get_proj_sector(pid, proj_map):
    p = proj_map.get(pid)
    if not p:
        return None
    raw = p['fields'].get('positioning_notes', '')
    if raw:
        try:
            n = json.loads(raw)
            s = n.get('sector', '')
            if s:
                for k in CAMPAIGN_MAP:
                    if k.lower() in s.lower() or s.lower() in k.lower():
                        return k
        except Exception:
            pass
    # fallback: analyst_notes on the project
    notes = p['fields'].get('analyst_notes', '')
    if notes:
        m = re.search(r'—\s*([^—\n]+)\s*$', notes.strip())
        if m:
            s = m.group(1).strip()
            for k in CAMPAIGN_MAP:
                if k.lower() in s.lower():
                    return k
    return None


def guess_sector_from_company(company_name):
    if not company_name:
        return None
    name_lower = company_name.lower()
    for sector, keywords in COMPANY_SECTOR_KEYWORDS.items():
        if any(kw.lower() in name_lower for kw in keywords):
            return sector
    return None


def update_contact_notes(record_id, new_notes):
    r = requests.patch(
        f'https://api.airtable.com/v0/{BASE_ID}/{CONTACTS_TABLE}/{record_id}',
        headers=AT_HEADERS,
        json={'fields': {'analyst_notes': new_notes}}
    )
    return r.ok, r.status_code


def main():
    print('=== ECAS Sector Attribution Fix ===\n')

    # --- Step 1: Fetch all contacts ---
    print('Fetching contacts...')
    all_contacts = fetch_all(CONTACTS_TABLE)
    print(f'  Total contacts: {len(all_contacts)}')

    unrouted = [c for c in all_contacts if not c['fields'].get('smartlead_campaign_id')]
    print(f'  Unrouted (no smartlead_campaign_id): {len(unrouted)}')

    # Sample of unrouted
    print('\n  Sample unrouted contacts:')
    for c in unrouted[:5]:
        f = c['fields']
        print(f'    {f.get("full_name")} @ {f.get("company_name")} | '
              f'projects: {f.get("projects", [])} | '
              f'notes: {f.get("analyst_notes", "")[:80]}')

    # --- Step 2: Fetch all projects ---
    print('\nFetching projects...')
    proj_records = fetch_all(PROJECTS_TABLE)
    proj_map = {r['id']: r for r in proj_records}
    print(f'  Projects loaded: {len(proj_map)}')

    # --- Step 3: Resolve sector via project link ---
    resolved_project = []   # (record_id, name, company, sector)
    still_unknown = []      # (record_id, name, company, notes)

    for c in unrouted:
        f = c['fields']
        proj_ids = f.get('projects', [])
        sector = None

        for pid in proj_ids:
            s = get_proj_sector(pid, proj_map)
            if s:
                sector = s
                break

        if sector:
            resolved_project.append((c['id'], f.get('full_name'), f.get('company_name'), sector))
        else:
            still_unknown.append((c['id'], f.get('full_name'), f.get('company_name'), f.get('analyst_notes', '')))

    print(f'\nStep 2 (project link): Resolved {len(resolved_project)}, still unknown: {len(still_unknown)}')

    # --- Step 4: Keyword fallback for still_unknown ---
    resolved_keyword = []
    truly_unknown = []

    for record_id, name, company, notes in still_unknown:
        guessed = guess_sector_from_company(company)
        if guessed:
            resolved_keyword.append((record_id, name, company, guessed))
        else:
            truly_unknown.append((record_id, name, company, notes))

    print(f'Step 3 (keyword fallback): Resolved {len(resolved_keyword)}, truly unknown: {len(truly_unknown)}')

    # --- Step 5: All resolved contacts ---
    all_resolved = resolved_project + resolved_keyword
    sector_counts = Counter(s for _, _, _, s in all_resolved)
    print(f'\nTotal resolved: {len(all_resolved)} / {len(unrouted)}')
    print('Sector distribution:')
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        print(f'  {sector}: {count}')

    if truly_unknown:
        print(f'\nTruly unknown ({len(truly_unknown)} contacts — no project link + no keyword match):')
        for _, name, company, notes in truly_unknown[:20]:
            print(f'  {name} @ {company} | notes: {notes[:60]}')

    # --- Step 6: Update analyst_notes in Airtable ---
    print('\nUpdating analyst_notes in Airtable...')
    ok_count = 0
    fail_count = 0

    for record_id, name, company, sector in all_resolved:
        new_notes = f'TIER 1 — {company} — {sector}'
        ok, status = update_contact_notes(record_id, new_notes)
        if ok:
            ok_count += 1
            source = 'project' if any(record_id == r[0] for r in resolved_project) else 'keyword'
            print(f'  [{source}] Updated {name} @ {company}: {sector}')
        else:
            fail_count += 1
            print(f'  FAIL ({status}): {name} @ {company}')
        time.sleep(0.15)

    print(f'\n=== Update Summary ===')
    print(f'  Updated OK:      {ok_count}')
    print(f'  Failed:          {fail_count}')
    print(f'  Truly unknown:   {len(truly_unknown)}')
    print(f'\nResolved via project link: {len(resolved_project)}')
    print(f'Resolved via keyword:      {len(resolved_keyword)}')
    print(f'\nReady for enrollment. Run:')
    print(f'  doppler run --project ecas --config dev -- python3.13 enroll_contacts_to_campaigns.py')


if __name__ == '__main__':
    main()
