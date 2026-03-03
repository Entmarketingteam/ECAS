from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import io
import logging
import httpx
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ECAS Scraper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDUCTO_API_KEY = os.environ.get("REDUCTO_API_KEY", "")

PJM_VA_COUNTIES = {
    "loudoun", "fauquier", "stafford", "prince william",
    "clarke", "warren",
}


# ── Request models ──────────────────────────────────────────────────────────────

class ScrapePdfRequest(BaseModel):
    url: str


class ScrapePageRequest(BaseModel):
    url: str
    wait_for: Optional[str] = None


class ErcotQueueRequest(BaseModel):
    csv_url: str


class PjmQueueRequest(BaseModel):
    queue_data: str  # raw JSON string from PJM Data Miner 2


# ── Endpoints ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "ecas-scraper"}


@app.post("/scrape-pdf")
async def scrape_pdf(req: ScrapePdfRequest):
    """
    Fetches a PDF from the given URL, sends it to Reducto AI for extraction,
    and returns the extracted text plus metadata.
    """
    if not REDUCTO_API_KEY:
        raise HTTPException(status_code=500, detail="REDUCTO_API_KEY not set")

    logger.info(f"scrape-pdf: fetching {req.url}")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: download the PDF
            pdf_resp = await client.get(req.url, follow_redirects=True)
            if pdf_resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch PDF: HTTP {pdf_resp.status_code}",
                )
            pdf_bytes = pdf_resp.content
            logger.info(f"scrape-pdf: downloaded {len(pdf_bytes)} bytes")

            # Step 2: send to Reducto AI for extraction
            # Reducto accepts a file upload or a URL — we send the raw bytes
            reducto_resp = await client.post(
                "https://v1.api.reducto.ai/parse",
                headers={"Authorization": f"Bearer {REDUCTO_API_KEY}"},
                files={"file": ("document.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"return_text": "true"},
            )

        if reducto_resp.status_code != 200:
            logger.error(f"Reducto error: {reducto_resp.status_code} {reducto_resp.text}")
            raise HTTPException(
                status_code=502,
                detail=f"Reducto API error: {reducto_resp.status_code} — {reducto_resp.text[:300]}",
            )

        reducto_data = reducto_resp.json()
        extracted_text = reducto_data.get("text") or reducto_data.get("content", "")
        num_pages = reducto_data.get("num_pages") or reducto_data.get("pages", 0)

        return {
            "text": extracted_text,
            "pages": num_pages,
            "source_url": req.url,
        }

    except httpx.RequestError as e:
        logger.error(f"scrape-pdf network error: {e}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")


@app.post("/scrape-page")
async def scrape_page(req: ScrapePageRequest):
    """
    Uses Playwright to render a JS-heavy page and return its HTML + extracted text.
    """
    logger.info(f"scrape-page: rendering {req.url}")
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
                    logger.warning(f"scrape-page: selector '{req.wait_for}' not found — continuing anyway")

            html = await page.content()
            title = await page.title()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        # Remove script/style noise before extracting text
        for tag in soup(["script", "style", "nav", "footer", "head"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        logger.info(f"scrape-page: got {len(html)} bytes HTML, title='{title}'")
        return {
            "html": html,
            "text": text,
            "title": title,
            "source_url": req.url,
        }

    except Exception as e:
        logger.error(f"scrape-page error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse-ercot-queue")
async def parse_ercot_queue(req: ErcotQueueRequest):
    """
    Downloads a CSV from ERCOT MIS and returns parsed rows as a JSON array.
    Expected columns vary by ERCOT report; we normalise to a standard schema.
    """
    logger.info(f"parse-ercot-queue: fetching {req.csv_url}")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(req.csv_url, follow_redirects=True)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch ERCOT CSV: HTTP {resp.status_code}",
            )

        csv_text = resp.text
        df = pd.read_csv(io.StringIO(csv_text), dtype=str)

        # Normalise column names: lowercase + strip whitespace
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Map common ERCOT column names to our standard schema
        col_map = {
            # project name variants
            "project_name": "project_name",
            "project": "project_name",
            "name": "project_name",
            # county
            "county": "county",
            # state (ERCOT is always TX)
            "state": "state",
            # MW
            "mw": "mw",
            "capacity_mw": "mw",
            "size_mw": "mw",
            "nameplate_mw": "mw",
            # status
            "status": "status",
            "queue_status": "status",
            # queue date
            "queue_date": "queue_date",
            "application_date": "queue_date",
            "submitted_date": "queue_date",
        }

        output_rows = []
        for _, row in df.iterrows():
            record: dict = {
                "project_name": None,
                "county": None,
                "state": "TX",  # ERCOT is Texas
                "mw": None,
                "status": None,
                "queue_date": None,
            }
            for raw_col, standard_col in col_map.items():
                if raw_col in df.columns and record[standard_col] is None:
                    val = row.get(raw_col)
                    if pd.notna(val) and str(val).strip():
                        record[standard_col] = str(val).strip()

            # Skip blank rows
            if not any(record.values()):
                continue
            output_rows.append(record)

        logger.info(f"parse-ercot-queue: returning {len(output_rows)} rows")
        return output_rows

    except pd.errors.ParserError as e:
        logger.error(f"CSV parse error: {e}")
        raise HTTPException(status_code=422, detail=f"CSV parse error: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")


@app.post("/parse-pjm-queue")
async def parse_pjm_queue(req: PjmQueueRequest):
    """
    Parses a PJM Data Miner 2 queue JSON response.
    Filters to Virginia counties relevant to ENT Agency's territory.
    """
    import json as json_lib

    logger.info("parse-pjm-queue: parsing PJM queue data")
    try:
        raw = json_lib.loads(req.queue_data)
    except json_lib.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")

    # PJM Data Miner 2 returns {"data": [...], "totalRows": N}
    rows = raw if isinstance(raw, list) else raw.get("data", raw.get("items", []))

    output_rows = []
    for item in rows:
        # Normalise keys
        item_lower = {k.lower().replace(" ", "_"): v for k, v in item.items()}

        county_raw = str(item_lower.get("county", "") or "").lower().strip()
        state_raw = str(item_lower.get("state", "") or "").upper().strip()

        # Filter: Virginia only, and one of our target counties
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

    logger.info(f"parse-pjm-queue: {len(output_rows)} VA projects after filtering")
    return output_rows
