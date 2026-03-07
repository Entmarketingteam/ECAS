"""
seed_historical_signals.py
Seeds Airtable signals_raw with historical politician trade + SEC 13F data
from ECAS-Signal-Report-2026-03-04.md
Run once to bootstrap scoring engine with real data.
"""

import os
import sys
import time
import requests
from datetime import datetime

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = "appoi8SzEJY8in57x"
SIGNALS_TABLE = "tblAFJnXToLTKeaNU"
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{SIGNALS_TABLE}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

SECTOR_MAP = {
    # Power & Grid Infrastructure
    "GEV": "Power & Grid Infrastructure",
    "ETN": "Power & Grid Infrastructure",
    "PWR": "Power & Grid Infrastructure",
    "NEE": "Power & Grid Infrastructure",
    "VST": "Power & Grid Infrastructure",
    "FSLR": "Power & Grid Infrastructure",
    "CEG": "Power & Grid Infrastructure",
    "SO": "Power & Grid Infrastructure",
    "DUK": "Power & Grid Infrastructure",
    "D": "Power & Grid Infrastructure",
    "CCJ": "Power & Grid Infrastructure",
    "ALB": "Power & Grid Infrastructure",
    "ENPH": "Power & Grid Infrastructure",
    "NXE": "Power & Grid Infrastructure",
    "UEC": "Power & Grid Infrastructure",
    "DNN": "Power & Grid Infrastructure",
    "AEP": "Power & Grid Infrastructure",
    # Defense & Government Services
    "PLTR": "Defense & Government Services",
    "LMT": "Defense & Government Services",
    "RTX": "Defense & Government Services",
    "GD": "Defense & Government Services",
    "NOC": "Defense & Government Services",
    "BA": "Defense & Government Services",
    "HII": "Defense & Government Services",
    "LHX": "Defense & Government Services",
    "KTOS": "Defense & Government Services",
    "BAH": "Defense & Government Services",
    "LDOS": "Defense & Government Services",
    "SAIC": "Defense & Government Services",
    "PSN": "Defense & Government Services",
    "MTZ": "Power & Grid Infrastructure",  # MasTec is grid construction
    "TXT": "Defense & Government Services",
    "CACI": "Defense & Government Services",
}

COMPANY_MAP = {
    "GEV": "GE Vernova", "ETN": "Eaton Corp", "PWR": "Quanta Services",
    "NEE": "NextEra Energy", "VST": "Vistra Corp", "FSLR": "First Solar",
    "CEG": "Constellation Energy", "SO": "Southern Company", "DUK": "Duke Energy",
    "D": "Dominion Energy", "CCJ": "Cameco Corp", "ALB": "Albemarle",
    "ENPH": "Enphase Energy", "NXE": "NexGen Energy", "UEC": "Uranium Energy",
    "DNN": "Denison Mines", "AEP": "American Electric Power",
    "PLTR": "Palantir Technologies", "LMT": "Lockheed Martin", "RTX": "RTX Corp",
    "GD": "General Dynamics", "NOC": "Northrop Grumman", "BA": "Boeing",
    "HII": "Huntington Ingalls", "LHX": "L3Harris Technologies",
    "KTOS": "Kratos Defense", "BAH": "Booz Allen Hamilton", "LDOS": "Leidos",
    "SAIC": "Science Applications", "PSN": "Parsons Corp", "MTZ": "MasTec",
    "TXT": "Textron", "CACI": "CACI International",
}


def insert_signal(signal_type, source, company_name, sector, signal_date, raw_content,
                  heat_score=0.0, notes=""):
    if "T" not in signal_date:
        signal_date = signal_date[:10] + "T00:00:00.000Z"

    fields = {
        "signal_type": signal_type,
        "source": "manual",  # only valid singleSelect option for these types
        "company_name": company_name,
        "sector": sector,
        "captured_at": signal_date,
        "raw_text": raw_content[:10000],
        "confidence_score": round(heat_score, 1),
        "processed": False,
    }
    if notes:
        fields["notes"] = notes[:5000]

    time.sleep(0.25)
    resp = requests.post(BASE_URL, headers=HEADERS, json={"fields": fields}, timeout=30)
    if resp.status_code == 200:
        print(f"  ✓ {signal_type} | {company_name} | {sector} | score={heat_score}")
        return resp.json().get("id")
    else:
        print(f"  ✗ {resp.status_code} | {company_name}: {resp.text[:200]}")
        return None


def seed_politician_trades():
    """Seed congressional trade signals from the report."""
    print("\n=== SEEDING POLITICIAN TRADE SIGNALS ===\n")

    # Key buys only (filtered to net-positive signals) from report
    trades = [
        # (date, politician, party, district, ticker, trade_type, amount, score)
        ("2025-11-18", "Gilbert Cisneros", "D", "CA31", "GEV", "Purchase", "$1,001–$15,000", 55),
        ("2025-11-18", "Gilbert Cisneros", "D", "CA31", "ETN", "Purchase", "$1,001–$15,000", 50),
        ("2025-11-18", "Gilbert Cisneros", "D", "CA31", "PLTR", "Purchase", "$1,001–$15,000", 55),
        ("2025-11-18", "Gilbert Cisneros", "D", "CA31", "LMT", "Purchase", "$1,001–$15,000", 48),
        ("2025-11-18", "Gilbert Cisneros", "D", "CA31", "PWR", "Purchase", "$1,001–$15,000", 48),
        ("2025-11-07", "Gilbert Cisneros", "D", "CA31", "PLTR", "Purchase", "$1,001–$15,000", 52),
        ("2025-11-12", "Gilbert Cisneros", "D", "CA31", "CCJ", "Purchase", "$15,001–$50,000", 45),
        ("2025-11-05", "Richard Dean McCormick", "R", "GA06", "NEE", "Purchase", "$1,001–$15,000", 40),
        ("2025-11-05", "Richard Dean McCormick", "R", "GA06", "LHX", "Purchase", "$1,001–$15,000", 38),
        ("2025-12-10", "David J. Taylor", "R", "OH02", "ETN", "Purchase", "$1,001–$15,000", 48),
        ("2025-12-11", "Dan Newhouse", "R", "WA04", "TXT", "Purchase", "$1,001–$15,000", 35),
        ("2025-12-19", "Gilbert Cisneros", "D", "CA31", "GEV", "Purchase", "$1,001–$15,000", 55),
        ("2025-12-22", "Jonathan Jackson", "D", "IL01", "PLTR", "Purchase", "$15,001–$50,000", 65),
        ("2025-12-22", "Roger Williams", "R", "TX25", "RTX", "Purchase", "$1,001–$15,000", 40),
        ("2025-12-02", "Jared Moskowitz", "D", "FL23", "SO", "Purchase", "$1,001–$15,000", 38),
        ("2026-01-09", "Gilbert Cisneros", "D", "CA31", "GEV", "Purchase", "$1,001–$15,000", 58),
        ("2026-01-09", "Gilbert Cisneros", "D", "CA31", "PLTR", "Purchase", "$1,001–$15,000", 60),
        ("2026-01-09", "Gilbert Cisneros", "D", "CA31", "GD", "Purchase", "$1,001–$15,000", 45),
        ("2026-01-09", "Gilbert Cisneros", "D", "CA31", "RTX", "Purchase", "$1,001–$15,000", 42),
        ("2026-01-09", "Gilbert Cisneros", "D", "CA31", "FSLR", "Purchase", "$1,001–$15,000", 45),
        ("2026-01-16", "Nancy Pelosi", "D", "CA11", "VST", "Purchase", "$100,001–$250,000", 75),
        ("2026-01-16", "David J. Taylor", "R", "OH02", "ETN", "Purchase", "$1,001–$15,000", 52),
        ("2026-01-16", "David J. Taylor", "R", "OH02", "AEP", "Purchase", "$1,001–$15,000", 42),
        ("2026-01-30", "Gilbert Cisneros", "D", "CA31", "PWR", "Purchase", "$1,001–$15,000", 50),
        ("2026-01-30", "Jonathan Jackson", "D", "IL01", "GEV", "Purchase", "$15,001–$50,000", 68),
    ]

    inserted = 0
    for date, politician, party, district, ticker, trade_type, amount, base_score in trades:
        company = COMPANY_MAP.get(ticker, ticker)
        sector = SECTOR_MAP.get(ticker, "Power & Grid Infrastructure")

        raw = (
            f"Congressional Trade: {trade_type}\n"
            f"Politician: {politician} ({party}-{district})\n"
            f"Ticker: ${ticker} — {company}\n"
            f"Transaction Date: {date}\n"
            f"Amount: {amount}\n"
            f"Source: House of Representatives STOCK Act PTR Filing\n"
            f"Filing: disclosures-clerk.house.gov"
        )

        rid = insert_signal(
            signal_type="politician_trade",
            source="House Stock Watcher",
            company_name=company,
            sector=sector,
            signal_date=date,
            raw_content=raw,
            heat_score=float(base_score),
            notes=f"{politician} ({party}-{district}): {trade_type} ${ticker} {amount} on {date}",
        )
        if rid:
            inserted += 1

    print(f"\nPolitician trades: {inserted}/{len(trades)} inserted")
    return inserted


def seed_hedge_fund_13f():
    """Seed SEC 13F signals — one signal per fund per top ticker."""
    print("\n=== SEEDING SEC 13F HEDGE FUND SIGNALS ===\n")

    # Top positions from report — grouped as aggregate signals per ticker
    # Format: (filing_date, fund, ticker, value_m, fund_count_for_ticker, score)
    positions = [
        # PLTR — $10B+ across 5 funds
        ("2026-02-17", "Citadel Advisors", "PLTR", 7601, 5, 80),
        ("2026-02-17", "Millennium Management", "PLTR", 890, 5, 72),
        ("2026-02-12", "Renaissance Technologies", "PLTR", 1564, 5, 75),
        ("2026-02-13", "Bridgewater Associates", "PLTR", 6, 5, 55),
        # GEV — $3B+ across 5 funds
        ("2026-02-17", "Citadel Advisors", "GEV", 1542, 5, 78),
        ("2026-02-17", "Millennium Management", "GEV", 200, 5, 65),
        ("2026-02-12", "Renaissance Technologies", "GEV", 226, 5, 68),
        ("2026-02-13", "Bridgewater Associates", "GEV", 435, 5, 72),
        ("2026-02-17", "Tiger Global Management", "GEV", 636, 5, 72),
        # ETN — $704M across 4 funds
        ("2026-02-17", "Citadel Advisors", "ETN", 435, 4, 72),
        ("2026-02-17", "Millennium Management", "ETN", 158, 4, 65),
        ("2026-02-12", "Renaissance Technologies", "ETN", 102, 4, 63),
        ("2026-02-13", "Bridgewater Associates", "ETN", 9, 4, 52),
        # LMT — $1.1B across 4 funds
        ("2026-02-17", "Citadel Advisors", "LMT", 849, 4, 72),
        ("2026-02-17", "Millennium Management", "LMT", 155, 4, 63),
        ("2026-02-12", "Renaissance Technologies", "LMT", 88, 4, 60),
        ("2026-02-13", "Bridgewater Associates", "LMT", 22, 4, 55),
        # VST — Pelosi-adjacent, $1.1B across 4 funds
        ("2026-02-17", "Citadel Advisors", "VST", 680, 4, 70),
        ("2026-02-17", "Millennium Management", "VST", 205, 4, 63),
        ("2026-02-12", "Renaissance Technologies", "VST", 168, 4, 62),
        ("2026-02-13", "Bridgewater Associates", "VST", 50, 4, 55),
        # PWR — $181M across 3 funds
        ("2026-02-17", "Citadel Advisors", "PWR", 148, 3, 62),
        ("2026-02-17", "Millennium Management", "PWR", 27, 3, 55),
        ("2026-02-13", "Bridgewater Associates", "PWR", 6, 3, 50),
        # RTX
        ("2026-02-17", "Citadel Advisors", "RTX", 658, 3, 60),
        ("2026-02-17", "Millennium Management", "RTX", 232, 3, 58),
        ("2026-02-12", "Renaissance Technologies", "RTX", 48, 3, 52),
        # MTZ — MasTec, grid construction
        ("2026-02-17", "Citadel Advisors", "MTZ", 45, 4, 55),
        ("2026-02-17", "Millennium Management", "MTZ", 159, 4, 62),
        ("2026-02-12", "Renaissance Technologies", "MTZ", 1, 4, 45),
        ("2026-02-13", "Bridgewater Associates", "MTZ", 2, 4, 45),
        # FSLR — solar infrastructure
        ("2026-02-17", "Citadel Advisors", "FSLR", 2002, 3, 65),
        ("2026-02-17", "Millennium Management", "FSLR", 114, 3, 58),
        ("2026-02-13", "Bridgewater Associates", "FSLR", 12, 3, 50),
        # CEG — Constellation Energy (nuclear)
        ("2026-02-17", "Citadel Advisors", "CEG", 867, 3, 63),
        ("2026-02-17", "Millennium Management", "CEG", 89, 3, 55),
        ("2026-02-13", "Bridgewater Associates", "CEG", 15, 3, 50),
        # NEE
        ("2026-02-17", "Citadel Advisors", "NEE", 473, 3, 60),
        ("2026-02-17", "Millennium Management", "NEE", 38, 3, 52),
        ("2026-02-13", "Bridgewater Associates", "NEE", 1, 3, 45),
        # GD
        ("2026-02-17", "Citadel Advisors", "GD", 211, 3, 58),
        ("2026-02-17", "Millennium Management", "GD", 94, 3, 52),
        ("2026-02-13", "Bridgewater Associates", "GD", 14, 3, 48),
    ]

    inserted = 0
    for filing_date, fund, ticker, value_m, fund_count, score in positions:
        company = COMPANY_MAP.get(ticker, ticker)
        sector = SECTOR_MAP.get(ticker, "Power & Grid Infrastructure")

        raw = (
            f"SEC 13F-HR Filing — Q4 2025 (Period ending Dec 31, 2025)\n"
            f"Fund: {fund}\n"
            f"Filing Date: {filing_date}\n"
            f"Ticker: ${ticker} — {company}\n"
            f"Position Value: ${value_m}M\n"
            f"Total funds holding this ticker: {fund_count}/6 tracked funds\n"
            f"Sector: {sector}\n"
            f"Source: SEC EDGAR 13F-HR submissions"
        )

        rid = insert_signal(
            signal_type="hedge_fund",
            source="SEC EDGAR 13F",
            company_name=company,
            sector=sector,
            signal_date=filing_date,
            raw_content=raw,
            heat_score=float(score),
            notes=f"{fund}: ${value_m}M in ${ticker} | {fund_count}/6 funds holding",
        )
        if rid:
            inserted += 1

    print(f"\nHedge fund 13F signals: {inserted}/{len(positions)} inserted")
    return inserted


if __name__ == "__main__":
    print("ECAS — Historical Signal Seeder")
    print(f"Base: {AIRTABLE_BASE_ID} | Table: {SIGNALS_TABLE}")
    print("="*50)

    pt_count = seed_politician_trades()
    hf_count = seed_hedge_fund_13f()

    print(f"\n{'='*50}")
    print(f"TOTAL SEEDED: {pt_count + hf_count} signals")
    print(f"  Politician trades: {pt_count}")
    print(f"  Hedge fund 13F:    {hf_count}")
    print("\nNext: trigger claude_extraction + sector_scoring via admin API")
