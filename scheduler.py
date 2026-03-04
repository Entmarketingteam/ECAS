"""
scheduler.py — APScheduler orchestrator for ECAS engine.
Replaces all 5 n8n workflows with in-process Python jobs.

Job schedule:
  - Daily 6am UTC:   Politician trade scan
  - Weekly Mon 7am:  SEC 13F hedge fund scan
  - Daily 7am UTC:   Government contract scan
  - Every 6h:        RSS feed aggregation
  - Daily 8am UTC:   Claude signal extraction (batch)
  - Daily 9am UTC:   Sector scoring + timeline
  - Daily 10am UTC:  Contact enrichment (high-score projects)
  - Daily 10:30am:   Smartlead enrollment
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
    logger.info("=== JOB: FERC Poller ===")
    try:
        from signals.ferc_poller import run_poller
        result = run_poller(push_to_airtable=True)
        logger.info(f"FERC done: {result}")
    except Exception as e:
        logger.error(f"FERC job failed: {e}", exc_info=True)


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

        # Push top sector insight to Slack
        if sector_scores and SLACK_ACCESS_TOKEN:
            top = sector_scores[0]
            _send_slack(
                f"*ECAS Sector Heat Update* | {datetime.utcnow().strftime('%Y-%m-%d')}\n"
                f":fire: *{top['sector']}*: {top['heat_score']}/100 → "
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

    # Daily signal collection
    scheduler.add_job(job_politician_trades, CronTrigger(hour=6, minute=0), id="politician_trades")
    scheduler.add_job(job_government_contracts, CronTrigger(hour=7, minute=0), id="gov_contracts")
    scheduler.add_job(job_ferc_poller, CronTrigger(hour=7, minute=30), id="ferc_poller")

    # Weekly heavy scan (Mondays)
    scheduler.add_job(job_sec_13f, CronTrigger(day_of_week="mon", hour=7, minute=0), id="sec_13f")
    scheduler.add_job(job_weekly_digest, CronTrigger(day_of_week="mon", hour=8, minute=0), id="weekly_digest")

    # RSS every 6 hours
    scheduler.add_job(job_rss_feeds, IntervalTrigger(hours=6), id="rss_feeds")

    # Processing pipeline (runs after collection)
    scheduler.add_job(job_claude_extraction, CronTrigger(hour=8, minute=0), id="claude_extraction")
    scheduler.add_job(job_sector_scoring, CronTrigger(hour=9, minute=0), id="sector_scoring")
    scheduler.add_job(job_enrichment, CronTrigger(hour=10, minute=0), id="enrichment")
    scheduler.add_job(job_smartlead_enrollment, CronTrigger(hour=10, minute=30), id="smartlead")

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
        "claude_extraction": job_claude_extraction,
        "sector_scoring": job_sector_scoring,
        "enrichment": job_enrichment,
        "smartlead": job_smartlead_enrollment,
        "weekly_digest": job_weekly_digest,
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
