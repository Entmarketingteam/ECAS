"""
storage/airtable.py — Airtable client for ECAS.

Field mappings (verified against live schema 2026-03-05):
  signals_raw:  signal_id, source(singleSelect), url, raw_text, captured_at(dateTime),
                processed, confidence_score, notes, signal_type, company_name, sector
  projects:     project_name, owner_company, stage(singleSelect), priority(singleSelect),
                icp_fit(singleSelect), confidence_score, analyst_notes(multilineText),
                scope_summary(multilineText), positioning_notes(multilineText),
                positioning_window_open, positioning_window_close,
                rfp_expected_date, source_url, state(singleSelect), assigned_to,
                stage_entered_at(dateTime)

  stage choices:   Identified | Researching | Outreach | Meeting Set | Proposal Sent |
                   Negotiating | Won | Lost | Dormant
  priority choices: High | Medium | Low  (case-sensitive)
  icp_fit choices:  Strong | Moderate | Weak | Unknown  (case-sensitive)
  state choices:    VA | TX  (expand in Airtable UI to add more states)

  contacts:     first_name, last_name, email, title, company_name, linkedin_url,
                phone, outreach_status, analyst_notes
  outreach_status choices: pending_review | approved | do_not_contact | in_sequence |
                            replied | meeting_booked | not_interested | unsubscribed
  deals:        deal_name, company_name, stage, contract_value, guaranteed_revenue,
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
        phase: str = "",
        est_budget_unlock_start: str = "",
        est_budget_unlock_end: str = "",
        website: str = "",
        state: str = "",
        employee_count: int = 0,
        description: str = "",
    ) -> str | None:
        """
        Create or update a project record. Returns record ID.

        Field mapping:
          company_name → owner_company + project_name
          heat_score   → confidence_score
          sector       → scope_summary
          notes        → analyst_notes
          phase + budget window + metadata → positioning_notes (JSON blob)
        """
        import json as _json

        existing = self._get("projects", {
            "filterByFormula": f"{{owner_company}}='{company_name}'",
            "maxRecords": 1,
        })

        analyst_notes = notes or (
            f"Sector: {sector} | Phase: {phase} | Signals: {signal_count} | "
            f"Employees: {employee_count}"
        ).strip(" |")

        # Store rich metadata as JSON in positioning_notes (parsed by hot signal + budget monitors)
        meta = {
            "sector": sector,
            "phase": phase,
            "est_budget_unlock_start": est_budget_unlock_start,
            "est_budget_unlock_end": est_budget_unlock_end,
            "website": website,
            "state": state,
            "employee_count": employee_count,
            "description": description,
            "updated_at": datetime.utcnow().isoformat(),
        }
        positioning_notes = _json.dumps({k: v for k, v in meta.items() if v})

        # Map our internal values to Airtable singleSelect choices (case-sensitive)
        _STAGE_MAP = {
            "prospect": "Identified",
            "researching": "Researching",
            "outreach": "Outreach",
            "active": "Outreach",
            "meeting": "Meeting Set",
            "proposal": "Proposal Sent",
            "negotiating": "Negotiating",
            "won": "Won",
            "closed_won": "Won",
            "lost": "Lost",
            "closed_lost": "Lost",
            "dormant": "Dormant",
        }
        _PRIORITY_MAP = {"high": "High", "medium": "Medium", "low": "Low"}
        _ICP_MAP = {
            "high": "Strong", "strong": "Strong",
            "medium": "Moderate", "moderate": "Moderate",
            "low": "Weak", "weak": "Weak",
            "unknown": "Unknown",
        }
        fields = {
            "project_name": company_name,
            "owner_company": company_name,
            "confidence_score": round(heat_score, 1),
            "analyst_notes": analyst_notes,
            "scope_summary": sector,
            "positioning_notes": positioning_notes,
        }

        mapped_stage = _STAGE_MAP.get(str(stage).lower(), "Identified")
        fields["stage"] = mapped_stage

        mapped_priority = _PRIORITY_MAP.get(str(priority).lower())
        if mapped_priority:
            fields["priority"] = mapped_priority

        mapped_icp = _ICP_MAP.get(str(icp_fit).lower())
        if mapped_icp:
            fields["icp_fit"] = mapped_icp

        # Note: state singleSelect field has limited choices in Airtable (VA, TX only).
        # State is stored in positioning_notes JSON instead to avoid 422 errors.
        # Expand choices in Airtable UI if you want to filter by state there.

        # Use dedicated positioning window fields for budget dates
        if est_budget_unlock_start:
            fields["positioning_window_open"] = est_budget_unlock_start
        if est_budget_unlock_end:
            fields["positioning_window_close"] = est_budget_unlock_end
        if website:
            fields["source_url"] = website[:255]

        if existing:
            record_id = existing[0]["id"]
            update = {
                "confidence_score": round(heat_score, 1),
                "analyst_notes": analyst_notes,
                "scope_summary": sector,
                "positioning_notes": positioning_notes,
            }
            if est_budget_unlock_start:
                update["positioning_window_open"] = est_budget_unlock_start
            if est_budget_unlock_end:
                update["positioning_window_close"] = est_budget_unlock_end
            self._patch("projects", record_id, update)
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
        outreach_status: str = "pending_review",
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
