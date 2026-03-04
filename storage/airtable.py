"""
storage/airtable.py — Airtable client for ECAS.

Field mappings match the actual Airtable schema (verified 2026-03-04):
  signals_raw: signal_id, source(singleSelect), url, raw_text, captured_at(dateTime),
               processed, confidence_score, notes, signal_type, company_name, sector
  projects:    project_name, owner_company, stage, priority, icp_fit, confidence_score,
               analyst_notes, scope_summary, stage_entered_at, positioning_notes
  contacts:    first_name, last_name, email, title, company_name, linkedin_url,
               phone, outreach_status, analyst_notes
  deals:       deal_name, company_name, stage, contract_value, guaranteed_revenue,
               close_notes, next_step, next_step_due
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

# Map our signal sources to valid singleSelect options in signals_raw.source
SOURCE_MAP = {
    "rss_news": "rss_feed",
    "gov_contract": "manual",
    "ferc_filing": "ferc_efts",
    "politician_trade": "manual",
    "hedge_fund": "manual",
}


def _to_airtable_datetime(date_str: str) -> str:
    """Convert YYYY-MM-DD or ISO string to Airtable dateTime format."""
    if not date_str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if "T" in date_str:
        # Already datetime — ensure Z suffix
        return date_str[:19] + ".000Z"
    # Date only → midnight UTC
    return date_str[:10] + "T00:00:00.000Z"


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

        Field mapping:
          raw_content     → raw_text
          heat_score      → confidence_score
          signal_date     → captured_at (dateTime)
          source string   → source (singleSelect, mapped via SOURCE_MAP)
        """
        airtable_source = SOURCE_MAP.get(signal_type, "manual")
        captured_at = _to_airtable_datetime(signal_date)

        fields = {
            "signal_type": signal_type,
            "source": airtable_source,
            "company_name": company_name,
            "sector": sector,
            "captured_at": captured_at,
            "raw_text": raw_content[:10000],
            "confidence_score": round(heat_score, 1),
            "processed": False,
        }
        # Use notes field for URL or extra info
        if notes:
            fields["notes"] = notes[:10000]
        elif source and source.startswith("http"):
            fields["url"] = source[:255]
        elif source:
            fields["notes"] = source[:10000]

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
            "notes": extracted_notes[:10000],
        })

    def get_unprocessed_signals(self, limit: int = 20) -> list[dict]:
        """Get signals that haven't been processed by Claude yet."""
        records = self._get("signals_raw", {
            "filterByFormula": "NOT({processed})",
            "maxRecords": limit,
            "sort[0][field]": "captured_at",
            "sort[0][direction]": "desc",
        })
        return records

    def get_signals_by_sector(self, sector: str, days: int = 90) -> list[dict]:
        """Get recent signals for a sector."""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000Z")
        records = self._get("signals_raw", {
            "filterByFormula": f"AND({{sector}}='{sector}', {{captured_at}} >= '{cutoff}')",
            "sort[0][field]": "confidence_score",
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
        """
        Create or update a project record. Returns record ID.

        Field mapping:
          company_name → owner_company (and project_name for primary field)
          heat_score   → confidence_score
          notes        → analyst_notes
          signal_count → stored in analyst_notes as context
        """
        existing = self._get("projects", {
            "filterByFormula": f"{{owner_company}}='{company_name}'",
            "maxRecords": 1,
        })

        analyst_notes = notes or f"Signals: {signal_count} | Sector: {sector}"

        fields = {
            "project_name": company_name,
            "owner_company": company_name,
            "confidence_score": round(heat_score, 1),
            "analyst_notes": analyst_notes,
        }
        if stage and stage in ("prospect", "active", "proposal", "closed_won", "closed_lost"):
            fields["stage"] = stage
        if priority and priority in ("high", "medium", "low"):
            fields["priority"] = priority
        if icp_fit and icp_fit in ("high", "medium", "low"):
            fields["icp_fit"] = icp_fit

        if existing:
            record_id = existing[0]["id"]
            self._patch("projects", record_id, {
                "confidence_score": round(heat_score, 1),
                "analyst_notes": analyst_notes,
            })
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
        """
        Create or update a contact. Returns record ID.

        Field mapping:
          company      → company_name (schema field name)
          notes        → analyst_notes
        """
        existing = self._get("contacts", {
            "filterByFormula": f"{{email}}='{email}'",
            "maxRecords": 1,
        })

        fields = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}".strip(),
            "title": title,
            "company_name": company,
            "outreach_status": outreach_status,
        }
        if linkedin_url:
            fields["linkedin_url"] = linkedin_url
        if phone:
            fields["phone"] = phone
        if notes:
            fields["analyst_notes"] = notes

        if existing:
            record_id = existing[0]["id"]
            patch = {}
            if notes:
                patch["analyst_notes"] = notes
            if outreach_status:
                patch["outreach_status"] = outreach_status
            if patch:
                self._patch("contacts", record_id, patch)
            return record_id
        else:
            result = self._post("contacts", fields)
            return result.get("id") if result else None

    def update_contact_status(self, record_id: str, status: str, notes: str = "") -> None:
        """Update a contact's outreach status."""
        fields = {"outreach_status": status}
        if notes:
            fields["analyst_notes"] = notes
        self._patch("contacts", record_id, fields)

    def get_contacts_by_company(self, company_name: str) -> list[dict]:
        """Get all contacts for a given company."""
        return self._get("contacts", {
            "filterByFormula": f"{{company_name}}='{company_name}'",
        })

    # ── Deals ──────────────────────────────────────────────────────────────────

    def upsert_deal(
        self,
        company_name: str,
        stage: str = "prospect",
        mrr_target: float = 12500.0,
        notes: str = "",
    ) -> str | None:
        """
        Create or update a deal record.

        Field mapping:
          mrr_target → contract_value (monthly retainer as annual equivalent)
          notes      → close_notes
        """
        existing = self._get("deals", {
            "filterByFormula": f"{{company_name}}='{company_name}'",
            "maxRecords": 1,
        })

        fields = {
            "deal_name": company_name,
            "company_name": company_name,
            "contract_value": mrr_target,
        }
        if stage:
            fields["stage"] = stage
        if notes:
            fields["close_notes"] = notes

        if existing:
            record_id = existing[0]["id"]
            update_fields = {}
            if stage:
                update_fields["stage"] = stage
            if notes:
                update_fields["close_notes"] = notes
            if update_fields:
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
