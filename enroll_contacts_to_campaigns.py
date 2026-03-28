#!/usr/bin/env python3
"""
Enroll ECAS contacts into correct Smartlead campaigns based on sector.
Campaigns are PAUSED so this is safe — nothing will send until manually activated.
"""
import os, requests, re, time, json
from collections import defaultdict

AT_KEY = os.environ['AIRTABLE_API_KEY']
SL_KEY = os.environ.get('SMARTLEAD_API_KEY') or os.environ.get('SMARTLEAD_API', '')
BASE_ID = 'appoi8SzEJY8in57x'
CONTACTS_TABLE = 'tblPBvTBuhwlS8AnS'
PROJECTS_TABLE = 'tbloen0rEkHttejnC'
AT_HEADERS = {'Authorization': f'Bearer {AT_KEY}', 'Content-Type': 'application/json'}

SECTOR_TO_CAMPAIGN = {
    'Power & Grid Infrastructure': 3005694,
    'Data Center & AI Infrastructure': 3040599,
    'Water & Wastewater': 3040600,
    'Industrial & Manufacturing Facilities': 3040601,
    'Defense': 3095136,
}

def fetch_all(table_id):
    records, offset = [], None
    while True:
        params = {'pageSize': 100}
        if offset: params['offset'] = offset
        r = requests.get(f'https://api.airtable.com/v0/{BASE_ID}/{table_id}',
                        headers=AT_HEADERS, params=params)
        data = r.json()
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset: break
    return records

def parse_sector_from_notes(notes):
    """Extract sector from analyst_notes — last segment after '—'"""
    if not notes: return None
    m = re.search(r'—\s*([^—\n]+)\s*$', notes.strip())
    if m:
        s = m.group(1).strip()
        # Match to known sectors
        for sector in SECTOR_TO_CAMPAIGN:
            if sector.lower() in s.lower() or s.lower() in sector.lower():
                return sector
    return None

def get_project_sector(project_id, projects_map):
    """Look up sector from linked project's analyst_notes or project_type."""
    proj = projects_map.get(project_id)
    if not proj: return None
    f = proj['fields']
    # Try sector from positioning_notes JSON
    notes_raw = f.get('positioning_notes', '')
    if notes_raw:
        try:
            notes = json.loads(notes_raw)
            sector = notes.get('sector', '')
            if sector:
                for s in SECTOR_TO_CAMPAIGN:
                    if s.lower() in sector.lower():
                        return s
        except: pass
    # Try analyst_notes
    return parse_sector_from_notes(f.get('analyst_notes', ''))

def enroll_in_smartlead(campaign_id, contact):
    """Enroll a single contact in a Smartlead campaign."""
    f = contact['fields']
    lead = {
        'email': f.get('email', ''),
        'first_name': f.get('first_name', ''),
        'last_name': f.get('last_name', ''),
        'company_name': f.get('company_name', ''),
        'custom_fields': {
            'title': f.get('title', ''),
            'linkedin_url': f.get('linkedin_url', ''),
        }
    }
    if not lead['email']:
        return False, 'no email'

    r = requests.post(
        f'https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads',
        params={'api_key': SL_KEY},
        json={'lead_list': [lead], 'settings': {'ignore_global_block_list': False, 'ignore_unsubscribe_list': False}}
    )
    if r.ok:
        return True, 'enrolled'
    elif r.status_code == 409 or 'already' in r.text.lower():
        return True, 'already_exists'
    else:
        return False, f'{r.status_code}: {r.text[:100]}'

def update_airtable_campaign(record_id, campaign_id):
    """Update smartlead_campaign_id in Airtable."""
    r = requests.patch(
        f'https://api.airtable.com/v0/{BASE_ID}/{CONTACTS_TABLE}/{record_id}',
        headers=AT_HEADERS,
        json={'fields': {'smartlead_campaign_id': str(campaign_id)}}
    )
    return r.ok

def main():
    print('Fetching contacts and projects...')
    contacts = fetch_all(CONTACTS_TABLE)
    projects_list = fetch_all(PROJECTS_TABLE)
    projects_map = {r['id']: r for r in projects_list}

    print(f'  Contacts: {len(contacts)}, Projects: {len(projects_map)}')

    # Filter: only contacts that don't have smartlead_campaign_id set
    to_route = [c for c in contacts if not c['fields'].get('smartlead_campaign_id')]
    print(f'  Contacts needing campaign assignment: {len(to_route)}')

    # Route each contact to a campaign
    by_campaign = defaultdict(list)
    skipped = {'defense': 0, 'unknown': 0, 'no_email': 0}

    for contact in to_route:
        f = contact['fields']
        if not f.get('email'):
            skipped['no_email'] += 1
            continue

        # Try sector from analyst_notes first
        sector = parse_sector_from_notes(f.get('analyst_notes', ''))

        # If unknown, try linked projects
        if not sector:
            for proj_id in f.get('projects', []):
                s = get_project_sector(proj_id, projects_map)
                if s:
                    sector = s
                    break

        if not sector:
            skipped['unknown'] += 1
            continue

        campaign_id = SECTOR_TO_CAMPAIGN.get(sector)
        if not campaign_id:
            skipped['defense'] += 1
            continue

        by_campaign[campaign_id].append((contact, sector))

    print(f'\nRouting summary:')
    for cid, contacts_list in by_campaign.items():
        print(f'  Campaign {cid}: {len(contacts_list)} contacts')
    print(f'  Skipped: {dict(skipped)}')

    # Enroll contacts
    enrolled_ok = 0
    enrolled_skip = 0
    failed = 0

    for campaign_id, contacts_list in by_campaign.items():
        print(f'\nEnrolling {len(contacts_list)} contacts into campaign {campaign_id}...')
        for contact, sector in contacts_list:
            ok, msg = enroll_in_smartlead(campaign_id, contact)
            if ok:
                if msg == 'already_exists':
                    enrolled_skip += 1
                else:
                    enrolled_ok += 1
                # Update Airtable regardless
                update_airtable_campaign(contact['id'], campaign_id)
            else:
                failed += 1
                print(f'  FAIL: {contact["fields"].get("email")} — {msg}')
            time.sleep(0.2)  # rate limit

    print(f'\n=== Done ===')
    print(f'  Enrolled: {enrolled_ok}')
    print(f'  Already existed: {enrolled_skip}')
    print(f'  Failed: {failed}')
    print(f'  Skipped (unknown/defense): {sum(skipped.values())}')

if __name__ == '__main__':
    main()
