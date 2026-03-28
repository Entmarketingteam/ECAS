#!/usr/bin/env python3
"""
Populate employee_count in project positioning_notes from Apollo.
Apollo /mixed_companies/search endpoint returns employee_count for company lookups.
"""
import os
import requests
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

APOLLO_KEY = os.environ['APOLLO_API_KEY']
AT_KEY = os.environ['AIRTABLE_API_KEY']
BASE_ID = 'appoi8SzEJY8in57x'
TABLE_ID = 'tbloen0rEkHttejnC'
AT_HEADERS = {'Authorization': f'Bearer {AT_KEY}', 'Content-Type': 'application/json'}


def fetch_all_projects():
    records, offset = [], None
    while True:
        params = {'pageSize': 100, 'fields[]': ['owner_company', 'positioning_notes']}
        if offset:
            params['offset'] = offset
        r = requests.get(
            f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}',
            headers=AT_HEADERS, params=params
        )
        r.raise_for_status()
        data = r.json()
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break
    return records


def get_apollo_employee_count(company_name, retry=True):
    """Search Apollo for company, return (employee_count, domain, matched_name)."""
    try:
        r = requests.post(
            'https://api.apollo.io/v1/organizations/search',
            headers={
                'Content-Type': 'application/json',
                'X-Api-Key': APOLLO_KEY,
            },
            json={
                'q_organization_name': company_name,
                'page': 1,
                'per_page': 1
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            orgs = data.get('organizations', [])
            if orgs:
                org = orgs[0]
                emp = org.get('estimated_num_employees') or org.get('num_employees') or 0
                domain = org.get('primary_domain', '')
                matched_name = org.get('name', '')
                return int(emp) if emp else 0, domain, matched_name
        elif r.status_code == 429:
            print(f'  [rate limit] Apollo throttled — sleeping 10s')
            time.sleep(10)
            if retry:
                return get_apollo_employee_count(company_name, retry=False)
        else:
            print(f'  [HTTP {r.status_code}] {company_name}: {r.text[:100]}')
    except Exception as e:
        print(f'  Apollo error for {company_name}: {e}')
    return 0, '', ''


def update_project_employee_count(record_id, current_notes_raw, employee_count, domain=''):
    """Update positioning_notes JSON with employee_count (and optionally domain)."""
    if current_notes_raw:
        try:
            notes = json.loads(current_notes_raw)
        except Exception:
            notes = {'raw': current_notes_raw}
    else:
        notes = {}

    notes['employee_count'] = employee_count
    if domain and not notes.get('domain'):
        notes['domain'] = domain

    r = requests.patch(
        f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}',
        headers=AT_HEADERS,
        json={'fields': {'positioning_notes': json.dumps(notes)}}
    )
    return r.status_code


def main():
    print('Fetching all projects from Airtable...')
    records = fetch_all_projects()
    print(f'Found {len(records)} projects total')

    # Identify records needing enrichment
    to_process = []
    already_done = 0
    no_company = 0

    for rec in records:
        company = rec['fields'].get('owner_company', '').strip()
        if not company:
            no_company += 1
            continue
        notes_raw = rec['fields'].get('positioning_notes', '')
        try:
            notes = json.loads(notes_raw) if notes_raw else {}
            if notes.get('employee_count', 0) > 0:
                already_done += 1
                continue
        except Exception:
            pass
        to_process.append(rec)

    print(f'  Already enriched (employee_count > 0): {already_done}')
    print(f'  No company name: {no_company}')
    print(f'  Need Apollo lookup: {len(to_process)}')
    print()

    if not to_process:
        print('Nothing to enrich!')
        return

    updated = 0
    failed = 0
    results = []

    for i, rec in enumerate(to_process):
        company = rec['fields'].get('owner_company', '').strip()
        notes_raw = rec['fields'].get('positioning_notes', '')

        print(f'[{i+1:3}/{len(to_process)}] {company[:45]:<45}', end=' ', flush=True)
        emp_count, domain, matched_name = get_apollo_employee_count(company)

        status = update_project_employee_count(rec['id'], notes_raw, emp_count, domain)
        if status == 200:
            updated += 1
            results.append({'company': company, 'emp': emp_count, 'domain': domain, 'matched': matched_name})
            print(f'-> {emp_count:>5} employees  [{matched_name[:30] if matched_name != company else "exact match"}]')
        else:
            failed += 1
            print(f'-> Airtable FAILED (HTTP {status})')

        # Rate limit: Apollo allows ~20 req/sec on most plans, be safe at ~3/sec
        time.sleep(0.35)

    # ── Distribution breakdown ──────────────────────────────────────────────────
    print()
    print('=' * 60)
    print('EMPLOYEE COUNT DISTRIBUTION')
    print('=' * 60)

    buckets = defaultdict(int)
    for r in results:
        emp = r['emp']
        if emp == 0:        buckets['0 (not found)'] += 1
        elif emp <= 10:     buckets['1-10'] += 1
        elif emp <= 50:     buckets['11-50'] += 1
        elif emp <= 100:    buckets['51-100'] += 1
        elif emp <= 200:    buckets['101-200'] += 1
        elif emp <= 500:    buckets['201-500'] += 1
        else:               buckets['500+'] += 1

    for label in ['0 (not found)', '1-10', '11-50', '51-100', '101-200', '201-500', '500+']:
        count = buckets[label]
        if count > 0:
            print(f'  {label:<18}: {count}')

    print()
    print(f'Updated:  {updated}/{len(to_process)} projects')
    print(f'Failed:   {failed}')
    print(f'Already had data: {already_done}')

    # Print top companies found
    if results:
        with_emp = sorted([r for r in results if r['emp'] > 0], key=lambda x: x['emp'], reverse=True)
        zero_emp = [r for r in results if r['emp'] == 0]
        print()
        print(f'Top companies by employee count ({len(with_emp)} found):')
        for r in with_emp[:20]:
            print(f"  {r['emp']:>6}  {r['company'][:45]}")
        if zero_emp:
            print(f'\n  {len(zero_emp)} companies returned 0 from Apollo:')
            for r in zero_emp[:10]:
                print(f"    - {r['company']}")
            if len(zero_emp) > 10:
                print(f'    ... and {len(zero_emp)-10} more')


if __name__ == '__main__':
    main()
