"""
scheduler.py — APScheduler orchestrator for ECAS engine.
Replaces all 5 n8n workflows with in-process Python jobs.

Job schedule:
  - Every 4h:        Politician trade scan (real-time signal detection)
  - Every 4h:        Government contract scan (real-time signal detection)
  - Every 4h:        FERC poller / EIA capacity (real-time signal detection)
  - Every 6h:        FERC EFTS filing poller (interconnection agreements, rate cases)
  - Every 12h:       PPA monitor (boosts PPA signals + polls PPA-focused feeds)
  - Weekly Mon 7am:  SEC 13F hedge fund scan
  - Weekly Tue 6am:  Earnings call transcript scan (FMP API — capex, SMR, grid language)
  - Every 6h:        RSS feed aggregation
  - Every 2h:        Claude signal extraction (keeps pace with frequent polls)
  - Every 3h:        Sector scoring + hot signal threshold check
  - Daily 10am UTC:  Contact enrichment (high-score projects)
  - Daily 10:30am:   Smartlead enrollment
  - Every 1h:        Budget window entry monitor (Day 1 outreach trigger)
  - Weekly Mon 8am:  Slack weekly digest
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

sys.path.insert(0, str(Path(__file__).parent))
from config import SLACK_ACCESS_TOKEN, SLACK_CHANNEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler")

_scheduler: BackgroundScheduler | None = None


# ── Job functions ──────────────────────────────────────────────────────────────

def job_politician_trades():
    logger.info("=== JOB: Politician Trades ===")
    try:
        from signals.political.house_senate_trades import run_scraper
        result = run_scraper()
        logger.info(f"Politician trades scraped: {result}")
        # Push sector-level signals to Airtable if thresholds met
        _push_politician_signals_to_airtable(result)
    except Exception as e:
        logger.error(f"Politician trades job failed: {e}", exc_info=True)


def _push_politician_signals_to_airtable(trade_result: dict) -> None:
    """Push politician trade summary signals to Airtable for qualifying sectors."""
    from storage.airtable import get_client
    from config import ALERT_THRESHOLDS
    at = get_client()

    breakdown = trade_result.get("sector_breakdown", {})
    politicians = trade_result.get("sector_politicians", {})

    for sector, count in breakdown.items():
        if count < ALERT_THRESHOLDS.get("min_politician_trades", 5):
            continue
        pols = politicians.get(sector, [])
        unique_pols = len(pols)
        if unique_pols < ALERT_THRESHOLDS.get("min_unique_politicians", 3):
            continue

        pol_list = ", ".join(pols[:5]) + ("..." if len(pols) > 5 else "")
        at.insert_signal(
            signal_type="politician_trade",
            source="House/Senate Stock Watcher",
            company_name=f"{sector} Sector",
            sector=sector,
            signal_date=__import__("datetime").datetime.utcnow().strftime("%Y-%m-%d"),
            raw_content=(
                f"{count} politician trades in {sector} in the last 90 days.\n"
                f"{unique_pols} unique politicians trading.\n"
                f"Politicians: {pol_list}"
            ),
            heat_score=min(20.0 + count * 0.5 + unique_pols * 2, 60.0),
        )
        logger.info(f"  Pushed politician signal: {sector} ({count} trades, {unique_pols} pols)")


def job_sec_13f():
    logger.info("=== JOB: SEC 13F Hedge Fund Scan ===")
    try:
        from signals.political.sec_13f import run_scraper
        result = run_scraper()
        logger.info(f"13F scan done: {result}")
    except Exception as e:
        logger.error(f"13F job failed: {e}", exc_info=True)


def job_earnings_transcripts():
    """
    Weekly scan of earnings call transcripts via FMP API.
    Detects Gemini-quantified triggers: capex hikes ≥20%, SMR/nuclear language,
    grid expansion, data center power demand, contract backlog growth, BD hiring.
    Pushes signals to Airtable → feeds into sector_scoring composite.
    Requires FMP_API_KEY in Doppler (paid plan for transcript access).
    """
    logger.info("=== JOB: Earnings Transcript Signal Scan ===")
    try:
        from signals.earnings_transcripts import run_scraper
        result = run_scraper(lookback_days=90, push_to_airtable=True)
        logger.info(f"Earnings transcripts done: {result}")

        if result.get("new_inserts", 0) > 0 and SLACK_ACCESS_TOKEN:
            breakdown = result.get("sector_breakdown", {})
            lines = [
                f":loudspeaker: *ECAS Earnings Signal Scan Complete*",
                f"*{result['new_inserts']} new signals* from {result['tickers_scanned']} tickers",
                "",
            ]
            for sector, count in breakdown.items():
                lines.append(f"• {sector}: {count} signals")
            lines.append("\nSignals ingested into sector scoring — check Airtable for hooks.")
            _send_slack("\n".join(lines))

    except Exception as e:
        logger.error(f"Earnings transcripts job failed: {e}", exc_info=True)


def job_government_contracts():
    logger.info("=== JOB: Government Contracts ===")
    try:
        from signals.political.government_contracts import run_scraper, push_top_contracts_to_airtable
        result = run_scraper()
        logger.info(f"Contracts scraped: {result}")
        # Push top contracts per sector to Airtable signals_raw
        for sector in result.get("sector_breakdown", {}):
            pushed = push_top_contracts_to_airtable(sector, limit=20, min_value_m=1.0)
            logger.info(f"  Pushed {pushed} contracts to Airtable for {sector}")
    except Exception as e:
        logger.error(f"Contracts job failed: {e}", exc_info=True)


def job_rss_feeds():
    logger.info("=== JOB: RSS Feed Aggregation ===")
    try:
        from signals.rss_aggregator import run_aggregator
        result = run_aggregator(push_to_airtable=True)
        logger.info(f"RSS done: {result}")
    except Exception as e:
        logger.error(f"RSS job failed: {e}", exc_info=True)


def job_ferc_poller():
    logger.info("=== JOB: EIA Capacity Poller (replaces FERC eLibrary) ===")
    try:
        from signals.ferc_poller import run_poller
        result = run_poller(push_to_airtable=True)
        logger.info(f"EIA done: {result}")
    except Exception as e:
        logger.error(f"EIA poller job failed: {e}", exc_info=True)


def job_pjm_poller():
    logger.info("=== JOB: PJM Territory Capacity Poller ===")
    try:
        from signals.pjm_poller import run_poller
        result = run_poller(push_to_airtable=True)
        logger.info(f"PJM done: {result}")
    except Exception as e:
        logger.error(f"PJM poller job failed: {e}", exc_info=True)


def job_ferc_rss():
    """
    FERC EFTS API poller — queries the FERC electronic filing search index for
    interconnection agreements, transmission construction filings, and rate cases.
    Replaces the dead FERC eLibrary scraper (Cloudflare-blocked SPA).
    Runs every 6h alongside the EIA capacity poller.
    """
    logger.info("=== JOB: FERC EFTS Filing Poller ===")
    try:
        from signals.ferc_rss_poller import run_poller
        result = run_poller(push_to_airtable=True)
        logger.info(f"FERC EFTS done: {result}")
    except Exception as e:
        logger.error(f"FERC EFTS job failed: {e}", exc_info=True)


def job_ppa_monitor():
    """
    PPA (Power Purchase Agreement) signal monitor.
    Two-pronged: boosts confidence scores on existing rss_news signals containing
    PPA keywords, then polls 6 PPA-focused RSS feeds for new deal announcements.
    PPA signed → developer must build plant → EPC needed within 3-6 months.
    Runs every 12h.
    """
    logger.info("=== JOB: PPA Monitor ===")
    try:
        from signals.ppa_monitor import run_monitor
        result = run_monitor(push_to_airtable=True)
        logger.info(f"PPA monitor done: {result}")
    except Exception as e:
        logger.error(f"PPA monitor job failed: {e}", exc_info=True)


def job_claude_extraction():
    logger.info("=== JOB: Claude Signal Extraction ===")
    try:
        from intelligence.claude_extractor import process_unprocessed_signals
        result = process_unprocessed_signals(batch_size=30)
        logger.info(f"Claude extraction done: {result}")
    except Exception as e:
        logger.error(f"Claude extraction job failed: {e}", exc_info=True)


def job_sector_scoring():
    logger.info("=== JOB: Sector Scoring + Timeline ===")
    try:
        from intelligence.sector_scoring import run_analysis
        from intelligence.timeline import run_analysis as run_timeline
        sector_scores = run_analysis()
        plans = run_timeline(sector_scores)
        logger.info(f"Scoring done: {len(sector_scores)} sectors")

        # Check for phase transitions — fires immediate Slack alert if any sector upgraded
        _check_phase_transitions(sector_scores)

        # Check individual company scores against hot signal threshold
        try:
            from storage.airtable import get_client
            at = get_client()
            projects = at._get("projects", {})
            _check_hot_signal_threshold(projects)
        except Exception as e:
            logger.warning(f"Hot signal check within sector scoring failed: {e}")

        # Heartbeat (only when no phase change happened — avoid double-ping)
        if sector_scores and SLACK_ACCESS_TOKEN:
            top = sector_scores[0]
            _send_slack(
                f"*ECAS Daily Heat* | {datetime.utcnow().strftime('%Y-%m-%d')}\n"
                f"{_PHASE_EMOJI.get(top['phase'], ':bar_chart:')} "
                f"*{top['sector']}*: {top['heat_score']}/100 → "
                f"{top['phase'].replace('_', ' ').title()}\n"
                f"Action: {top.get('phase_config', {}).get('action', '')}"
            )
    except Exception as e:
        logger.error(f"Sector scoring job failed: {e}", exc_info=True)


def job_enrichment():
    logger.info("=== JOB: Contact Enrichment ===")
    try:
        from enrichment.clay_enricher import run_enricher
        result = run_enricher(min_heat_score=50.0)
        logger.info(f"Enrichment done: {result}")
    except Exception as e:
        logger.error(f"Enrichment job failed: {e}", exc_info=True)


def job_smartlead_enrollment():
    logger.info("=== JOB: Smartlead Enrollment ===")
    try:
        from outreach.smartlead import enroll_airtable_contacts
        result = enroll_airtable_contacts(min_heat_score=50.0)
        logger.info(f"Smartlead enrollment done: {result}")
        if result.get("enrolled") and SLACK_ACCESS_TOKEN:
            _send_slack(
                f"*ECAS Outreach Update*: {result['enrolled']} contacts enrolled in Smartlead "
                f"({result['skipped']} skipped, {result['errors']} errors)"
            )
    except Exception as e:
        logger.error(f"Smartlead enrollment job failed: {e}", exc_info=True)


def job_usaspending_hunt():
    """
    Weekly hunt via USASpending.gov free API.
    Finds EPC contractors actively winning federal contracts in defense + energy.
    Contract dollar amounts = revenue proxy for ICP filtering ($5M-$200M federal = $10M-$400M total).
    CAGE codes cross-reference against SHIELD IDIQ awardees already in pipeline.
    Runs Saturdays 5am UTC — before directory_hunt (Sundays) and weekly digest (Mondays).
    """
    logger.info("=== JOB: USASpending Contract Hunter ===")
    try:
        from signals.usaspending_hunter import run_usaspending_hunt
        result = run_usaspending_hunt(days_back=365)
        logger.info(f"USASpending hunt done: {result}")

        total_created = sum(r.get("created", 0) for r in result.values())
        if total_created > 0 and SLACK_ACCESS_TOKEN:
            lines = [":us: *ECAS USASpending Hunt Complete*"]
            for sector, r in result.items():
                lines.append(
                    f"• {sector}: {r['companies_found']} companies found "
                    f"(${r['total_contract_value_m']:.0f}M total contracts) "
                    f"→ {r['created']} new, {r['skipped']} already tracked"
                )
            _send_slack("\n".join(lines))
    except Exception as e:
        logger.error(f"USASpending hunt job failed: {e}", exc_info=True)


def job_job_posting_monitor():
    """
    Twice-weekly job posting scan via SerpAPI Google Jobs.
    Companies hiring estimators + BD directors = active pipeline = highest conversion moment.
    Boosts confidence score of existing pipeline companies, creates new records for unknowns.
    Runs Wednesdays + Saturdays 7am UTC to catch weekly job posting cycles.
    """
    logger.info("=== JOB: Job Posting Monitor (Hiring Surge Detector) ===")
    try:
        from signals.job_posting_monitor import run_job_monitor
        result = run_job_monitor()
        logger.info(f"Job posting monitor done: {result}")

        total_surge = sum(r.get("surge_companies", 0) for r in result.values())
        total_boosted = sum(r.get("boosted", 0) for r in result.values())
        if (total_surge > 0 or total_boosted > 0) and SLACK_ACCESS_TOKEN:
            lines = [":briefcase: *ECAS Hiring Surge Alert*"]
            for sector, r in result.items():
                lines.append(
                    f"• {sector}: {r['surge_companies']} companies surging "
                    f"({r['total_open_roles']} open roles) "
                    f"→ {r.get('created', 0)} new, {r.get('boosted', 0)} score-boosted"
                )
            lines.append("\n_Hiring surge = active pipeline. High conversion probability._")
            _send_slack("\n".join(lines))
    except Exception as e:
        logger.error(f"Job posting monitor job failed: {e}", exc_info=True)


def job_directory_hunt():
    """
    Weekly hunt: SAM.gov Entity API + MapYourShow conference exhibitors + ENR rankings.
    Finds ICP companies that signal-based scraping misses — companies actively
    registered for government contracts, paying to exhibit at grid conferences,
    or ranked in ENR specialty contractor lists.
    Runs Sundays 6am UTC so fresh leads are ready for Monday enrichment.
    """
    logger.info("=== JOB: Directory Hunt (SAM.gov + Conferences + ENR) ===")
    try:
        from signals.directory_hunter import run_directory_hunt
        result = run_directory_hunt(dry_run=False, limit=500)
        logger.info(f"Directory hunt done: {result}")

        if result.get("created", 0) > 0 and SLACK_ACCESS_TOKEN:
            source_lines = "\n".join(
                f"• {k}: {v} companies" for k, v in result.get("source_counts", {}).items()
            )
            _send_slack(
                f":mag: *ECAS Directory Hunt Complete*\n"
                f"*{result['created']} new companies* added to pipeline\n\n"
                f"Sources:\n{source_lines}\n\n"
                f"_Skipped: {result.get('skipped', 0)} (already in pipeline). "
                f"Enrichment runs Monday 10am._"
            )
    except Exception as e:
        logger.error(f"Directory hunt job failed: {e}", exc_info=True)


def job_populate_projects():
    """
    The missing link: sector scores → specific companies to call.

    1. Pull current sector heat scores
    2. For each sector above threshold (40/100), search Apollo for ICP companies
    3. Upsert into Airtable projects with sector, phase, budget window
    4. Fire immediate enrichment for high-priority companies (heat > 55)

    Runs daily at 5am UTC, before enrichment (10am) and Smartlead (10:30am).
    Also runs on demand via /admin/run/populate_projects.
    """
    logger.info("=== JOB: Populate Projects (ICP Hunter) ===")
    try:
        from signals.icp_hunter import run_icp_hunt
        from intelligence.sector_scoring import run_analysis

        sector_scores = run_analysis()
        result = run_icp_hunt(sector_scores=sector_scores)

        logger.info(
            f"ICP Hunt done: {result['total_upserted']} companies → Airtable "
            f"across {len(result['sectors_hunted'])} sectors"
        )

        # Immediately enrich any high-priority new companies (score > 55)
        hot_sectors = [s for s in result["sectors_hunted"] if s["heat_score"] >= 55]
        if hot_sectors:
            logger.info(f"Hot sectors found — triggering immediate enrichment for {len(hot_sectors)} sectors")
            try:
                from enrichment.clay_enricher import run_enricher
                enrich_result = run_enricher(min_heat_score=55.0)
                logger.info(f"Immediate enrichment: {enrich_result}")
            except Exception as e:
                logger.warning(f"Immediate enrichment after hunt failed: {e}")

        if SLACK_ACCESS_TOKEN and result["total_upserted"] > 0:
            lines = [
                f":dart: *ECAS ICP Hunt Complete*",
                f"*{result['total_upserted']} companies* added/updated in pipeline",
                "",
            ]
            for s in result["sectors_hunted"]:
                lines.append(
                    f"• {s['sector']}: {s['companies_upserted']} companies "
                    f"({s['heat_score']:.0f}/100)"
                )
            _send_slack("\n".join(lines))

    except Exception as e:
        logger.error(f"Populate projects job failed: {e}", exc_info=True)


def job_dedup_projects():
    """Weekly safety net: delete duplicate project records (same owner_company)."""
    logger.info("=== JOB: Dedup Projects ===")
    try:
        import requests as _req
        from storage.airtable import get_client
        at = get_client()

        all_records: list[dict] = []
        offset = None
        while True:
            params: dict = {"fields[]": ["owner_company", "confidence_score"]}
            if offset:
                params["offset"] = offset
            resp = _req.get(
                f"https://api.airtable.com/v0/appoi8SzEJY8in57x/tbloen0rEkHttejnC",
                headers=at.headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            all_records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break

        # Group by normalised company name
        from collections import defaultdict
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in all_records:
            key = r.get("fields", {}).get("owner_company", "").lower().replace("'", "").strip()
            if key:
                groups[key].append(r)

        deleted = 0
        for key, records in groups.items():
            if len(records) <= 1:
                continue
            # Keep highest confidence_score; break ties by created order (first wins)
            records.sort(key=lambda r: r.get("fields", {}).get("confidence_score", 0), reverse=True)
            for dupe in records[1:]:
                del_resp = _req.delete(
                    f"https://api.airtable.com/v0/appoi8SzEJY8in57x/tbloen0rEkHttejnC/{dupe['id']}",
                    headers=at.headers,
                    timeout=30,
                )
                if del_resp.status_code == 200:
                    deleted += 1
                    logger.info(f"Dedup: deleted {dupe['id']} ({records[0].get('fields',{}).get('owner_company')})")

        logger.info(f"Dedup complete — {deleted} duplicate records removed from {len(all_records)} total")
    except Exception as e:
        logger.error(f"Dedup projects job failed: {e}", exc_info=True)


def job_weekly_digest():
    logger.info("=== JOB: Weekly Digest ===")
    try:
        from intelligence.sector_scoring import run_analysis
        from intelligence.timeline import run_analysis as timeline
        from storage.airtable import get_client

        sector_scores = run_analysis()
        plans = timeline(sector_scores)
        at = get_client()

        # Count pipeline
        contacts = at._get("contacts", {})
        projects = at._get("projects", {})
        enrolled = sum(
            1 for c in contacts
            if c.get("fields", {}).get("outreach_status") == "enrolled"
        )

        msg_lines = [
            f"*ECAS Weekly Intelligence Digest* | {datetime.utcnow().strftime('%Y-%m-%d')}",
            "",
            "*Sector Heat Scores:*",
        ]
        for s in sector_scores:
            msg_lines.append(
                f"• {s['sector']}: {s['heat_score']}/100 "
                f"[{s['phase'].replace('_', ' ').title()}]"
            )

        msg_lines.extend([
            "",
            f"*Pipeline:* {len(projects)} tracked companies | {len(contacts)} contacts | "
            f"{enrolled} enrolled in Smartlead",
            "",
            "*Top Action:*",
        ])
        if plans:
            top = plans[0]
            msg_lines.append(
                f"{top['sector']}: {top['immediate_action']}"
            )

        if SLACK_ACCESS_TOKEN:
            _send_slack("\n".join(msg_lines))
        logger.info("Weekly digest sent")

    except Exception as e:
        logger.error(f"Weekly digest job failed: {e}", exc_info=True)


# ── Hot signal threshold ───────────────────────────────────────────────────────

_HOT_SIGNAL_THRESHOLD = 55.0
_HOT_SIGNAL_DB_TABLE = "hot_signal_history"


def _ensure_hot_signal_table() -> None:
    import sqlite3
    from config import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {_HOT_SIGNAL_DB_TABLE} (
            company_name TEXT PRIMARY KEY,
            heat_score REAL NOT NULL,
            alerted_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _get_last_hot_alert(company_name: str) -> str | None:
    import sqlite3
    from config import DB_PATH
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            f"SELECT alerted_at FROM {_HOT_SIGNAL_DB_TABLE} WHERE company_name = ?",
            (company_name,)
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _record_hot_alert(company_name: str, heat_score: float) -> None:
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(f"""
        INSERT INTO {_HOT_SIGNAL_DB_TABLE} (company_name, heat_score, alerted_at)
        VALUES (?, ?, ?)
        ON CONFLICT(company_name) DO UPDATE SET
            heat_score = excluded.heat_score,
            alerted_at = excluded.alerted_at
    """, (company_name, heat_score, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def _parse_project_meta(fields: dict) -> dict:
    """
    Extract project metadata. Primary source: dedicated Airtable fields.
    Fallback: positioning_notes JSON blob.
    """
    import json as _json
    meta = {}
    raw = fields.get("positioning_notes", "")
    if raw:
        try:
            meta = _json.loads(raw)
        except Exception:
            pass

    # Prefer dedicated fields over JSON blob
    if fields.get("positioning_window_open"):
        meta["est_budget_unlock_start"] = fields["positioning_window_open"]
    if fields.get("positioning_window_close"):
        meta["est_budget_unlock_end"] = fields["positioning_window_close"]
    if fields.get("scope_summary"):
        meta["sector"] = fields["scope_summary"]

    return meta


def _check_hot_signal_threshold(projects: list[dict]) -> None:
    """
    Fire immediately when a company's heat score crosses 55/100.
    Skips companies already alerted within the last 24 hours to avoid spam.
    Triggers Slack alert + Smartlead enrollment without waiting for daily batch.
    """
    _ensure_hot_signal_table()

    now = datetime.utcnow()
    for project in projects:
        fields = project.get("fields", {})
        company = fields.get("owner_company") or fields.get("project_name", "Unknown")
        score = float(fields.get("confidence_score", 0) or 0)

        if score < _HOT_SIGNAL_THRESHOLD:
            continue

        # Cooldown: skip if alerted in the last 24h
        last_alert = _get_last_hot_alert(company)
        if last_alert:
            from datetime import timedelta
            last_dt = datetime.fromisoformat(last_alert)
            if (now - last_dt).total_seconds() < 86400:
                logger.debug(f"[HOT] {company} already alerted recently, skipping")
                continue

        meta = _parse_project_meta(fields)
        sector = meta.get("sector") or fields.get("scope_summary", "Unknown")
        phase = (meta.get("phase") or "unknown").replace("_", " ").title()
        budget_start = meta.get("est_budget_unlock_start", "TBD")
        budget_end = meta.get("est_budget_unlock_end", "TBD")
        ticker = meta.get("ticker", "")

        emoji = ":rocket:" if score >= 70 else ":zap:"
        msg = (
            f"{emoji} *HOT SIGNAL — {company}* {emoji}\n\n"
            f"*Score:* {score}/100 (threshold: {_HOT_SIGNAL_THRESHOLD})\n"
            f"*Sector:* {sector} | *Phase:* {phase}\n"
            f"*Budget Window:* {budget_start} → {budget_end}\n"
            f"*Ticker:* {ticker or 'N/A'}\n\n"
            f"*Action:* Enroll in Smartlead NOW — do not wait for daily batch.\n"
            f"_Score just crossed {_HOT_SIGNAL_THRESHOLD}/100 threshold._"
        )
        logger.info(f"[HOT SIGNAL] {company}: {score}/100 — firing immediate alert")
        if SLACK_ACCESS_TOKEN:
            _send_slack(msg)

        # Immediate Smartlead enrollment
        try:
            from outreach.smartlead import enroll_airtable_contacts
            result = enroll_airtable_contacts(
                min_heat_score=_HOT_SIGNAL_THRESHOLD,
                company_filter=company,
            )
            logger.info(f"[HOT SIGNAL] Smartlead enrollment for {company}: {result}")
        except Exception as e:
            logger.warning(f"[HOT SIGNAL] Smartlead enrollment failed for {company}: {e}")

        _record_hot_alert(company, score)


def job_hot_signal_check():
    """
    Runs every time sector_scoring completes (called inline) and also
    available as a standalone manual trigger via /admin/run/hot_signal_check.
    """
    logger.info("=== JOB: Hot Signal Threshold Check ===")
    try:
        from storage.airtable import get_client
        at = get_client()
        projects = at._get("projects", {})
        _check_hot_signal_threshold(projects)
        logger.info(f"Hot signal check done: {len(projects)} projects scanned")
    except Exception as e:
        logger.error(f"Hot signal check failed: {e}", exc_info=True)


# ── Budget window monitor ──────────────────────────────────────────────────────

_BUDGET_WINDOW_DB_TABLE = "budget_window_alerts"


def _ensure_budget_window_table() -> None:
    import sqlite3
    from config import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {_BUDGET_WINDOW_DB_TABLE} (
            company_name TEXT PRIMARY KEY,
            window_start TEXT NOT NULL,
            alerted_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _already_sent_window_alert(company_name: str, window_start: str) -> bool:
    import sqlite3
    from config import DB_PATH
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            f"SELECT window_start FROM {_BUDGET_WINDOW_DB_TABLE} WHERE company_name = ?",
            (company_name,)
        ).fetchone()
        conn.close()
        return row is not None and row[0] == window_start
    except Exception:
        return False


def _record_window_alert(company_name: str, window_start: str) -> None:
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(f"""
        INSERT INTO {_BUDGET_WINDOW_DB_TABLE} (company_name, window_start, alerted_at)
        VALUES (?, ?, ?)
        ON CONFLICT(company_name) DO UPDATE SET
            window_start = excluded.window_start,
            alerted_at = excluded.alerted_at
    """, (company_name, window_start, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def job_budget_window_monitor():
    """
    Runs every hour. Checks Airtable projects for companies whose
    est_budget_unlock_start == today. Fires Day 1 outreach Slack alert
    + immediate Smartlead enrollment for any new window entries.
    """
    logger.info("=== JOB: Budget Window Monitor ===")
    try:
        _ensure_budget_window_table()
        from storage.airtable import get_client
        at = get_client()
        projects = at._get("projects", {})
        today = datetime.utcnow().strftime("%Y-%m-%d")

        triggered = 0
        for project in projects:
            fields = project.get("fields", {})
            company = fields.get("owner_company") or fields.get("project_name", "Unknown")
            heat_score = float(fields.get("confidence_score", 0) or 0)

            meta = _parse_project_meta(fields)
            window_start = meta.get("est_budget_unlock_start", "")

            if not window_start:
                continue

            # Normalize to YYYY-MM-DD
            window_date = str(window_start)[:10]
            if window_date != today:
                continue

            if _already_sent_window_alert(company, window_date):
                logger.debug(f"[BUDGET] {company} window alert already sent for {window_date}")
                continue

            sector = meta.get("sector") or fields.get("scope_summary", "Unknown")
            window_end = meta.get("est_budget_unlock_end", "TBD")
            ticker = meta.get("ticker", "")
            phase = (meta.get("phase") or "unknown").replace("_", " ").title()

            msg = (
                f":calendar: *BUDGET WINDOW OPENS TODAY — {company}* :calendar:\n\n"
                f"*DAY 1 OF BUDGET UNLOCK WINDOW*\n"
                f"*Company:* {company} ({ticker or 'private'})\n"
                f"*Sector:* {sector} | *Phase:* {phase}\n"
                f"*Heat Score:* {heat_score}/100\n"
                f"*Window:* {window_date} → {window_end}\n\n"
                f"*Action:* Contact NOW — Day 1 is highest conversion probability.\n"
                f"Bypass RFP process. Direct outreach beats competitive bidding.\n"
                f"_Budget window entry alert — fired automatically on Day 1._"
            )

            logger.info(f"[BUDGET WINDOW] DAY 1 alert for {company} (window: {window_date})")
            if SLACK_ACCESS_TOKEN:
                _send_slack(msg)

            # Enroll in Smartlead immediately regardless of score (budget window = max urgency)
            try:
                from outreach.smartlead import enroll_airtable_contacts
                result = enroll_airtable_contacts(
                    min_heat_score=0.0,
                    company_filter=company,
                )
                logger.info(f"[BUDGET WINDOW] Smartlead enrollment for {company}: {result}")
            except Exception as e:
                logger.warning(f"[BUDGET WINDOW] Smartlead enrollment failed for {company}: {e}")

            _record_window_alert(company, window_date)
            triggered += 1

        logger.info(f"Budget window monitor done: {triggered} Day 1 alerts fired")
    except Exception as e:
        logger.error(f"Budget window monitor failed: {e}", exc_info=True)


# ── Phase transition tracking ─────────────────────────────────────────────────

_PHASE_ORDER = {
    "early_signal": 1,
    "confirmed_signal": 2,
    "imminent_unlock": 3,
    "active_spend": 4,
}

_PHASE_EMOJI = {
    "early_signal": ":seedling:",
    "confirmed_signal": ":zap:",
    "imminent_unlock": ":rotating_light:",
    "active_spend": ":fire:",
}


def _ensure_phase_history_table() -> None:
    import sqlite3
    from config import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sector_phase_history (
            sector TEXT PRIMARY KEY,
            phase TEXT NOT NULL,
            heat_score REAL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _get_stored_phase(sector: str) -> str | None:
    import sqlite3
    from config import DB_PATH
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            "SELECT phase FROM sector_phase_history WHERE sector = ?", (sector,)
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _update_stored_phase(sector: str, phase: str, heat_score: float) -> None:
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        INSERT INTO sector_phase_history (sector, phase, heat_score, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sector) DO UPDATE SET
            phase = excluded.phase,
            heat_score = excluded.heat_score,
            updated_at = excluded.updated_at
    """, (sector, phase, heat_score, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def _check_phase_transitions(sector_scores: list[dict]) -> None:
    """Compare new scores to stored phases. Fire immediate Slack alert on upgrade."""
    _ensure_phase_history_table()
    from config import TIMELINE_PHASES

    for s in sector_scores:
        sector = s["sector"]
        new_phase = s["phase"]
        new_score = s["heat_score"]
        old_phase = _get_stored_phase(sector)

        old_rank = _PHASE_ORDER.get(old_phase, 0)
        new_rank = _PHASE_ORDER.get(new_phase, 0)

        if new_rank > old_rank:
            # Phase upgraded — fire immediate alert
            phase_cfg = TIMELINE_PHASES.get(new_phase, {})
            action = phase_cfg.get("action", "Review and act.")
            months = phase_cfg.get("months_to_unlock", "?")
            emoji = _PHASE_EMOJI.get(new_phase, ":bell:")

            arrow = f"{old_phase.replace('_', ' ').title()} → {new_phase.replace('_', ' ').title()}"
            msg = (
                f"{emoji} *ECAS PHASE TRANSITION — ACT NOW* {emoji}\n\n"
                f"*Sector:* {sector}\n"
                f"*Heat Score:* {new_score}/100\n"
                f"*Phase:* {arrow}\n"
                f"*Budget Timeline:* {months} months to deployment\n\n"
                f"*Recommended Action:*\n{action}\n\n"
                f"_This alert fired automatically — sector just crossed the threshold._"
            )
            logger.info(f"[PHASE TRANSITION] {sector}: {old_phase} → {new_phase} ({new_score}/100)")
            if SLACK_ACCESS_TOKEN:
                _send_slack(msg)

        _update_stored_phase(sector, new_phase, new_score)


# ── Slack helper ───────────────────────────────────────────────────────────────

def _send_slack(text: str) -> None:
    try:
        import requests
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"channel": SLACK_CHANNEL, "text": text},
            timeout=10,
        )
        if not resp.json().get("ok"):
            logger.warning(f"Slack send failed: {resp.json()}")
    except Exception as e:
        logger.warning(f"Slack error: {e}")


# ── Scheduler setup ────────────────────────────────────────────────────────────

def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    # ── High-frequency signal collection (every 4h) ──────────────────────────
    # These are the highest-value sources — real-time detection is the edge.
    # Staggered start offsets prevent API thundering herd on the same minute.
    scheduler.add_job(job_politician_trades, IntervalTrigger(hours=4, start_date="2000-01-01 00:00:00"), id="politician_trades")
    scheduler.add_job(job_government_contracts, IntervalTrigger(hours=4, start_date="2000-01-01 01:20:00"), id="gov_contracts")
    scheduler.add_job(job_ferc_poller, IntervalTrigger(hours=4, start_date="2000-01-01 02:40:00"), id="ferc_poller")
    # PJM territory capacity — every 12h (EIA data refreshes ~monthly, but frequent
    # queries catch any data corrections + keeps the job in the active signal loop)
    scheduler.add_job(job_pjm_poller, IntervalTrigger(hours=12, start_date="2000-01-01 03:20:00"), id="pjm_poller")

    # ── RSS every 6 hours ────────────────────────────────────────────────────
    scheduler.add_job(job_rss_feeds, IntervalTrigger(hours=6), id="rss_feeds")

    # ── FERC EFTS filing poller (every 6h, offset from RSS to avoid thundering herd) ─
    scheduler.add_job(job_ferc_rss, IntervalTrigger(hours=6, start_date="2000-01-01 03:00:00"), id="ferc_rss")

    # ── PPA monitor (every 12h — boosts existing signals + polls PPA RSS feeds) ─
    scheduler.add_job(job_ppa_monitor, IntervalTrigger(hours=12, start_date="2000-01-01 01:00:00"), id="ppa_monitor")

    # ── Weekly heavy scan (Mondays) ──────────────────────────────────────────
    scheduler.add_job(job_sec_13f, CronTrigger(day_of_week="mon", hour=7, minute=0), id="sec_13f")
    scheduler.add_job(job_weekly_digest, CronTrigger(day_of_week="mon", hour=8, minute=0), id="weekly_digest")
    # Earnings transcripts — Tuesdays 6am UTC (earnings cycle is quarterly; weekly scan is sufficient)
    scheduler.add_job(job_earnings_transcripts, CronTrigger(day_of_week="tue", hour=6, minute=0), id="earnings_transcripts")

    # ── Processing pipeline (every 2-3h to keep pace with frequent polls) ───
    scheduler.add_job(job_claude_extraction, IntervalTrigger(hours=2), id="claude_extraction")
    scheduler.add_job(job_sector_scoring, IntervalTrigger(hours=3), id="sector_scoring")

    # ── Outreach (daily batch — still fine, hot signals bypass this) ─────────
    scheduler.add_job(job_enrichment, CronTrigger(hour=10, minute=0), id="enrichment")
    scheduler.add_job(job_smartlead_enrollment, CronTrigger(hour=10, minute=30), id="smartlead")

    # ── ICP company population (daily 5am — before enrichment at 10am) ──────
    scheduler.add_job(job_populate_projects, CronTrigger(hour=5, minute=0), id="populate_projects")

    # ── Discovery layer (contract data + hiring signals + conference exhibitors) ─
    # USASpending: Saturdays 5am — federal contract winners, revenue-proxied ICP list
    scheduler.add_job(job_usaspending_hunt, CronTrigger(day_of_week="sat", hour=5, minute=0), id="usaspending_hunt")
    # Job postings: Wed + Sat 7am — hiring surge = active pipeline signal
    scheduler.add_job(job_job_posting_monitor, CronTrigger(day_of_week="wed,sat", hour=7, minute=0), id="job_posting_monitor")
    # Directory hunt: Sundays 6am — MapYourShow conferences + ENR rankings
    scheduler.add_job(job_directory_hunt, CronTrigger(day_of_week="sun", hour=6, minute=0), id="directory_hunt")
    scheduler.add_job(job_dedup_projects, CronTrigger(day_of_week="sun", hour=7, minute=0), id="dedup_projects")

    # ── Real-time alert jobs ─────────────────────────────────────────────────
    # Hot signal check runs inline inside job_sector_scoring, but also
    # available as a standalone manual trigger (not scheduled separately).
    # Budget window monitor: every hour so Day 1 alert fires within 60 min.
    scheduler.add_job(job_budget_window_monitor, IntervalTrigger(hours=1), id="budget_window_monitor")

    return scheduler


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    _scheduler = create_scheduler()
    _scheduler.start()
    logger.info(f"Scheduler started with {len(_scheduler.get_jobs())} jobs")
    for job in _scheduler.get_jobs():
        logger.info(f"  → {job.id}: {job.trigger}")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def run_job_now(job_id: str) -> dict:
    """Manually trigger a job by ID. Used by admin API endpoints."""
    job_map = {
        "politician_trades": job_politician_trades,
        "sec_13f": job_sec_13f,
        "gov_contracts": job_government_contracts,
        "rss_feeds": job_rss_feeds,
        "ferc_poller": job_ferc_poller,
        "pjm_poller": job_pjm_poller,
        "claude_extraction": job_claude_extraction,
        "sector_scoring": job_sector_scoring,
        "enrichment": job_enrichment,
        "smartlead": job_smartlead_enrollment,
        "weekly_digest": job_weekly_digest,
        "earnings_transcripts": job_earnings_transcripts,
        "hot_signal_check": job_hot_signal_check,
        "budget_window_monitor": job_budget_window_monitor,
        "populate_projects": job_populate_projects,
        "directory_hunt": job_directory_hunt,
        "dedup_projects": job_dedup_projects,
        "usaspending_hunt": job_usaspending_hunt,
        "job_posting_monitor": job_job_posting_monitor,
        "ferc_rss": job_ferc_rss,
        "ppa_monitor": job_ppa_monitor,
    }

    fn = job_map.get(job_id)
    if not fn:
        return {"error": f"Unknown job: {job_id}", "available": list(job_map.keys())}

    logger.info(f"Manual trigger: {job_id}")
    try:
        fn()
        return {"status": "ok", "job": job_id, "ran_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Manual job {job_id} failed: {e}", exc_info=True)
        return {"status": "error", "job": job_id, "error": str(e)}


def get_scheduler_status() -> dict:
    """Return current scheduler status and next run times."""
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": True,
        "job_count": len(jobs),
        "jobs": sorted(jobs, key=lambda x: x.get("next_run") or ""),
    }
