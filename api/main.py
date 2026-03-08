"""
api/main.py — FastAPI entrypoint for ECAS engine.

Endpoints:
  GET  /health              → Service health + scheduler status
  GET  /admin/status        → Full scheduler + pipeline status
  POST /admin/run/{job_id}  → Manually trigger any scheduled job
  GET  /admin/signals       → Recent signals from Airtable
  GET  /admin/scores        → Current sector heat scores
  POST /admin/enroll        → Manually enroll a lead in Smartlead
  POST /admin/generate-sequence → Generate cold email sequence via Claude (optional Smartlead push)
  POST /scrape-pdf          → PDF extraction via Reducto
  POST /scrape-page         → Playwright page scrape
  POST /parse-ercot-queue   → Parse ERCOT CSV
  POST /parse-pjm-queue     → Parse PJM JSON (VA filter)
"""

import io
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import REDUCTO_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup / Shutdown ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler on boot
    try:
        from scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler started")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")
    yield
    # Shutdown
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="ECAS Engine",
    version="2.0.0",
    description="Enterprise Contract Acquisition System — signal intelligence + outreach engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PJM_VA_COUNTIES = {
    "loudoun", "fauquier", "stafford", "prince william",
    "clarke", "warren",
}


# ── Request models ─────────────────────────────────────────────────────────────

class ScrapePdfRequest(BaseModel):
    url: str


class ScrapePageRequest(BaseModel):
    url: str
    wait_for: Optional[str] = None


class ErcotQueueRequest(BaseModel):
    csv_url: str


class PjmQueueRequest(BaseModel):
    queue_data: str


class EnrollLeadRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    company: str
    title: str
    sector: str = "Power & Grid Infrastructure"
    heat_score: float = 0.0
    campaign_id: Optional[str] = None


# ── Core endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    from scheduler import get_scheduler_status
    status = get_scheduler_status()
    return {
        "status": "ok",
        "service": "ecas-engine",
        "version": "2.0.0",
        "scheduler_running": status.get("running", False),
        "job_count": status.get("job_count", 0),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Admin endpoints ────────────────────────────────────────────────────────────

@app.get("/admin/status")
def admin_status():
    """Full pipeline status: scheduler jobs + Airtable counts."""
    from scheduler import get_scheduler_status
    sched = get_scheduler_status()

    try:
        from storage.airtable import get_client
        at = get_client()
        signals = at._get("signals_raw", {"maxRecords": 1})
        projects = at._get("projects", {"maxRecords": 1})
        contacts = at._get("contacts", {"maxRecords": 1})
    except Exception:
        signals = projects = contacts = []

    return {
        "scheduler": sched,
        "airtable": {
            "signals_raw": "accessible" if signals is not None else "error",
            "projects": "accessible" if projects is not None else "error",
            "contacts": "accessible" if contacts is not None else "error",
        },
    }


@app.post("/admin/run/{job_id}")
async def run_job(job_id: str, background_tasks: BackgroundTasks):
    """Trigger a scheduled job manually. Runs in background."""
    from scheduler import run_job_now
    # Run in background so endpoint returns immediately
    background_tasks.add_task(run_job_now, job_id)
    return {
        "status": "triggered",
        "job": job_id,
        "message": f"Job '{job_id}' is running in background",
        "triggered_at": datetime.utcnow().isoformat(),
    }


@app.get("/admin/signals")
def admin_signals(limit: int = 20, sector: str = None):
    """View recent signals from Airtable."""
    try:
        from storage.airtable import get_client
        at = get_client()
        if sector:
            records = at.get_signals_by_sector(sector, days=30)[:limit]
        else:
            records = at._get("signals_raw", {
                "maxRecords": limit,
                "sort[0][field]": "captured_at",
                "sort[0][direction]": "desc",
            })
        return {
            "count": len(records),
            "signals": [
                {
                    "id": r.get("id"),
                    "type": r.get("fields", {}).get("signal_type"),
                    "company": r.get("fields", {}).get("company_name"),
                    "sector": r.get("fields", {}).get("sector"),
                    "heat_score": r.get("fields", {}).get("confidence_score"),
                    "signal_date": r.get("fields", {}).get("captured_at"),
                    "processed": r.get("fields", {}).get("processed", False),
                }
                for r in records
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/scores")
def admin_scores():
    """Run sector scoring and return current heat scores."""
    try:
        from intelligence.sector_scoring import run_analysis
        from intelligence.timeline import run_analysis as run_timeline
        scores = run_analysis()
        plans = run_timeline(scores)
        return {
            "scored_at": datetime.utcnow().isoformat(),
            "sectors": [
                {
                    "sector": s["sector"],
                    "heat_score": s["heat_score"],
                    "phase": s["phase"],
                    "months_to_unlock": plans[i].get("months_to_unlock") if i < len(plans) else None,
                    "action": plans[i].get("immediate_action") if i < len(plans) else None,
                    "components": s.get("components", {}),
                }
                for i, s in enumerate(scores)
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/enroll")
def admin_enroll(req: EnrollLeadRequest):
    """Manually enroll a single lead into Smartlead."""
    from outreach.smartlead import enroll_lead
    result = enroll_lead(
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        company=req.company,
        title=req.title,
        sector=req.sector,
        heat_score=req.heat_score,
        campaign_id=req.campaign_id,
    )
    return result


# ── Existing scraper endpoints (preserved from v1) ─────────────────────────────

@app.post("/scrape-pdf")
async def scrape_pdf(req: ScrapePdfRequest):
    if not REDUCTO_API_KEY:
        raise HTTPException(status_code=500, detail="REDUCTO_API_KEY not set")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            pdf_resp = await client.get(req.url, follow_redirects=True)
            if pdf_resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Failed to fetch PDF: HTTP {pdf_resp.status_code}")
            pdf_bytes = pdf_resp.content

            reducto_resp = await client.post(
                "https://v1.api.reducto.ai/parse",
                headers={"Authorization": f"Bearer {REDUCTO_API_KEY}"},
                files={"file": ("document.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"return_text": "true"},
            )

        if reducto_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Reducto error: {reducto_resp.status_code}")

        data = reducto_resp.json()
        return {
            "text": data.get("text") or data.get("content", ""),
            "pages": data.get("num_pages") or data.get("pages", 0),
            "source_url": req.url,
        }
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {e}")


@app.post("/scrape-page")
async def scrape_page(req: ScrapePageRequest):
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            await page.goto(req.url, wait_until="networkidle", timeout=45000)
            if req.wait_for:
                try:
                    await page.wait_for_selector(req.wait_for, timeout=10000)
                except Exception:
                    pass
            html = await page.content()
            title = await page.title()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "head"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return {"html": html, "text": text, "title": title, "source_url": req.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse-ercot-queue")
async def parse_ercot_queue(req: ErcotQueueRequest):
    import pandas as pd
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(req.csv_url, follow_redirects=True)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"HTTP {resp.status_code}")

        df = pd.read_csv(io.StringIO(resp.text), dtype=str)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        col_map = {
            "project_name": "project_name", "project": "project_name", "name": "project_name",
            "county": "county", "state": "state",
            "mw": "mw", "capacity_mw": "mw", "size_mw": "mw", "nameplate_mw": "mw",
            "status": "status", "queue_status": "status",
            "queue_date": "queue_date", "application_date": "queue_date", "submitted_date": "queue_date",
        }

        output_rows = []
        for _, row in df.iterrows():
            record = {k: None for k in ["project_name", "county", "state", "mw", "status", "queue_date"]}
            record["state"] = "TX"
            for raw_col, std_col in col_map.items():
                if raw_col in df.columns and record[std_col] is None:
                    val = row.get(raw_col)
                    if pd.notna(val) and str(val).strip():
                        record[std_col] = str(val).strip()
            if any(record.values()):
                output_rows.append(record)

        return output_rows
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {e}")


@app.post("/parse-pjm-queue")
async def parse_pjm_queue(req: PjmQueueRequest):
    import json as json_lib
    try:
        raw = json_lib.loads(req.queue_data)
    except json_lib.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")

    rows = raw if isinstance(raw, list) else raw.get("data", raw.get("items", []))
    output_rows = []
    for item in rows:
        item_lower = {k.lower().replace(" ", "_"): v for k, v in item.items()}
        county_raw = str(item_lower.get("county", "") or "").lower().strip()
        state_raw = str(item_lower.get("state", "") or "").upper().strip()
        if state_raw not in ("VA", "VIRGINIA"):
            continue
        if not any(vc in county_raw for vc in PJM_VA_COUNTIES):
            continue
        output_rows.append({
            "project_name": item_lower.get("project_name") or item_lower.get("name"),
            "county": item_lower.get("county"),
            "state": "VA",
            "mw": item_lower.get("capacity_mw") or item_lower.get("mw"),
            "status": item_lower.get("status") or item_lower.get("queue_status"),
            "queue_date": item_lower.get("queue_date") or item_lower.get("submitted_date"),
        })

    return output_rows


# ── Sequence Generator ─────────────────────────────────────────────────────────

class GenerateSequenceRequest(BaseModel):
    sector: str
    push_to_smartlead: bool = False
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    campaign_name: Optional[str] = None


@app.post("/admin/generate-sequence")
async def generate_sequence(req: GenerateSequenceRequest):
    """
    Generate a sector-specific cold email sequence using live signal data + Claude.

    If push_to_smartlead=true, also creates the Smartlead campaign and uploads all emails.
    Requires from_name and from_email when push_to_smartlead=true.

    Example:
        POST /admin/generate-sequence
        {"sector": "Defense", "push_to_smartlead": false}

        POST /admin/generate-sequence
        {"sector": "Defense", "push_to_smartlead": true,
         "from_name": "Ethan", "from_email": "ethan@contractmotion.com"}
    """
    from outreach.sequence_generator import generate_sequence as gen_seq, generate_and_push

    valid_sectors = list(__import__("config", fromlist=["TARGET_SECTORS"]).TARGET_SECTORS.keys())
    if req.sector not in valid_sectors:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sector '{req.sector}'. Valid: {valid_sectors}"
        )

    try:
        if req.push_to_smartlead:
            if not req.from_name or not req.from_email:
                raise HTTPException(
                    status_code=422,
                    detail="from_name and from_email are required when push_to_smartlead=true"
                )
            result = generate_and_push(
                sector=req.sector,
                from_name=req.from_name,
                from_email=req.from_email,
                campaign_name=req.campaign_name,
            )
            return {
                "status": "created",
                "sector": req.sector,
                "campaign_id": result["campaign_id"],
                "campaign_name": result["campaign_name"],
                "emails_uploaded": result["emails_uploaded"],
                "smartlead_url": result["smartlead_url"],
                "heat_score": result["sequence"]["heat_score"],
                "phase": result["sequence"]["phase"],
                "preview": {
                    "email_1_subject": result["sequence"]["emails"][0]["subject"],
                    "email_2_subject": result["sequence"]["emails"][1]["subject"],
                    "email_3_subject": result["sequence"]["emails"][2]["subject"],
                    "email_4_subject": result["sequence"]["emails"][3]["subject"],
                },
            }
        else:
            sequence = gen_seq(req.sector)
            return {
                "status": "generated",
                "sector": req.sector,
                "heat_score": sequence["heat_score"],
                "phase": sequence["phase"],
                "signal_context": sequence["signal_context"],
                "generated_at": sequence["generated_at"],
                "emails": sequence["emails"],
            }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[API] generate-sequence failed for {req.sector}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
