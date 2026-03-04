"""
storage/airtable.py — Airtable client for ECAS.

All writes go through this module. Handles rate limiting, deduplication,
and field mapping for the 4 core tables.
"""

import logging
import time
from datetime import datetime
from typing import Any

import requests

from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLES

logger = logging.getLogger(__name__)

BASE_URL = "https://api.airtable.com/v0"
RATE_LIMIT_DELAY = 0.25  # 4 requests/sec (Airtable limit: 5/sec)


class AirtableClient:
    def __init__(self):
        if not AIRTABLE_API_KEY:
            raise RuntimeError("AIRTABLE_API_KEY not set")
        self.headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        }

    def _url(self, table_key: str) -> str:
        table_id = AIRTABLE_TABLES[table_key]
        return f"{BASE_URL}/{AIRTABLE_BASE_ID}/{table_id}"

    def _get(self, table_key: str, params: dict = None) -> list[dict]:
        """Fetch records from a table with optional filter."""
        url = self._url(table_key)
        records = []
        offset = None
        while True:
            p = params.copy() if params else {}
            if offset:
                p["offset"] = offset
            try:
                time.sleep(RATE_LIMIT_DELAY)
                resp = requests.get(url, headers=self.headers, params=p, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                records.extend(data.get("records", []))
                offset = data.get("offset")
                if not offset:
                    break
            except requests.RequestException as e:
                logger.error(f"Airtable GET {table_key} error: {e}")
                break
        return records

    def _post(self, table_key: str, fields: dict) -> dict | None:
        """Create a new record."""
        try:
            time.sleep(RATE_LIMIT_DELAY)
            resp = requests.post(
                self._url(table_key),
                headers=self.headers,
                json={"fields": fields},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Airtable POST {table_key} error: {e} | fields={fields}")
            return None

    def _patch(self, table_key: str, record_id: str, fields: dict) -> dict | None:
        """Update an existing record."""
        try:
            time.sleep(RATE_LIMIT_DELAY)
            resp = requests.patch(
                f"{self._url(table_key)}/{record_id}",
                headers=self.headers,
                json={"fields": fields},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Airtable PATCH {table_key}/{record_id} error: {e}")
            return None

    # ── Signals ────────────────────────────────────────────────────────────────

    def insert_signal(
        self,
        signal_type: str,
        source: str,
        company_name: str,
        sector: str,
        signal_date: str,
        raw_content: str,
        ticker: str = "",
        heat_score: float = 0.0,
        notes: str = "",
    ) -> str | None:
        """
        Insert a new signal into signals_raw. Returns Airtable record ID or None.
        Does not deduplicate — caller should check before calling.
        """
        # Ensure signal_date is YYYY-MM-DD only (Airtable date field)
        clean_date = signal_date[:10] if signal_date else datetime.utcnow().strftime("%Y-%m-%d")

        fields = {
            "signal_type": signal_type,
            "source": source,
            "company_name": company_name,
            "sector": sector,
            "signal_date": clean_date,
            "raw_content": raw_content[:10000],  # Airtable text field limit
            "heat_score": round(heat_score, 1),
            "processed": False,
        }
        if ticker:
            fields["ticker"] = ticker
        if notes:
            fields["notes"] = notes

        result = self._post("signals_raw", fields)
        if result:
            record_id = result.get("id")
            logger.info(f"Inserted signal: {signal_type} | {company_name} | {sector}")
            return record_id
        return None

    def mark_signal_processed(self, record_id: str, extracted_notes: str) -> None:
        """Mark a signal as processed after Claude extraction."""
        self._patch("signals_raw", record_id, {
            "processed": True,
            "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
            "notes": extracted_notes[:10000],
        })

    def get_unprocessed_signals(self, limit: int = 20) -> list[dict]:
        """Get signals that haven't been processed by Claude yet."""
        records = self._get("signals_raw", {
            "filterByFormula": "NOT({processed})",
            "maxRecords": limit,
            "sort[0][field]": "signal_date",
            "sort[0][direction]": "desc",
        })
        return records

    def get_signals_by_sector(self, sector: str, days: int = 90) -> list[dict]:
        """Get recent signals for a sector."""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        records = self._get("signals_raw", {
            "filterByFormula": f"AND({{sector}}='{sector}', {{signal_date}} >= '{cutoff}')",
            "sort[0][field]": "heat_score",
            "sort[0][direction]": "desc",
        })
        return records

    # ── Projects (EPCs we're targeting) ────────────────────────────────────────

    def upsert_project(
        self,
        company_name: str,
        sector: str = "Power & Grid Infrastructure",
        heat_score: float = 0.0,
        signal_count: int = 0,
        stage: str = "prospect",
        priority: str = "medium",
        icp_fit: str = "medium",
        notes: str = "",
    ) -> str | None:
        """Create or update a project record. Returns record ID."""
        # Check if exists
        existing = self._get("projects", {
            "filterByFormula": f"{{company_name}}='{company_name}'",
            "maxRecords": 1,
        })

        fields = {
            "company_name": company_name,
            "sector": sector,
            "heat_score": round(heat_score, 1),
            "signal_count": signal_count,
        }
        if stage:
            fields["stage"] = stage
        if priority:
            fields["priority"] = priority
        if icp_fit:
            fields["icp_fit"] = icp_fit
        if notes:
            fields["notes"] = notes

        if existing:
            record_id = existing[0]["id"]
            # Don't overwrite stage/priority on updates
            update_fields = {
                "heat_score": round(heat_score, 1),
                "signal_count": signal_count,
            }
            if notes:
                update_fields["notes"] = notes
            self._patch("projects", record_id, update_fields)
            return record_id
        else:
            result = self._post("projects", fields)
            return result.get("id") if result else None

    def get_projects(self, stage: str = None) -> list[dict]:
        """Get all projects, optionally filtered by stage."""
        params = {}
        if stage:
            params["filterByFormula"] = f"{{stage}}='{stage}'"
        return self._get("projects", params)

    # ── Contacts ───────────────────────────────────────────────────────────────

    def upsert_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        title: str,
        company: str,
        linkedin_url: str = "",
        phone: str = "",
        outreach_status: str = "not_contacted",
        notes: str = "",
    ) -> str | None:
        """Create or update a contact. Returns record ID."""
        existing = self._get("contacts", {
            "filterByFormula": f"{{email}}='{email}'",
            "maxRecords": 1,
        })

        fields = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company": company,
            "outreach_status": outreach_status,
        }
        if linkedin_url:
            fields["linkedin_url"] = linkedin_url
        if phone:
            fields["phone"] = phone
        if notes:
            fields["notes"] = notes

        if existing:
            record_id = existing[0]["id"]
            self._patch("contacts", record_id, {"notes": notes} if notes else {})
            return record_id
        else:
            result = self._post("contacts", fields)
            return result.get("id") if result else None

    def update_contact_status(self, record_id: str, status: str, notes: str = "") -> None:
        """Update a contact's outreach status."""
        fields = {"outreach_status": status}
        if notes:
            fields["notes"] = notes
        self._patch("contacts", record_id, fields)

    def get_contacts_by_company(self, company_name: str) -> list[dict]:
        """Get all contacts for a given company."""
        return self._get("contacts", {
            "filterByFormula": f"{{company}}='{company_name}'",
        })

    # ── Deals ──────────────────────────────────────────────────────────────────

    def upsert_deal(
        self,
        company_name: str,
        stage: str = "prospect",
        mrr_target: float = 12500.0,
        notes: str = "",
    ) -> str | None:
        """Create or update a deal record."""
        existing = self._get("deals", {
            "filterByFormula": f"{{company_name}}='{company_name}'",
            "maxRecords": 1,
        })

        fields = {
            "company_name": company_name,
            "stage": stage,
            "mrr_target": mrr_target,
        }
        if notes:
            fields["notes"] = notes

        if existing:
            record_id = existing[0]["id"]
            update_fields = {"stage": stage}
            if notes:
                update_fields["notes"] = notes
            self._patch("deals", record_id, update_fields)
            return record_id
        else:
            result = self._post("deals", fields)
            return result.get("id") if result else None


# Singleton
_client: AirtableClient | None = None


def get_client() -> AirtableClient:
    global _client
    if _client is None:
        _client = AirtableClient()
    return _client
