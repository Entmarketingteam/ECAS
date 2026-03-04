"""
config.py — Central configuration for ECAS engine.
All secrets pulled from environment variables (Doppler → Railway).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── Database (SQLite — intermediate cache for deduplication) ─────────────────
DB_PATH = BASE_DIR / "database" / "tracker.db"

# ─── Airtable ─────────────────────────────────────────────────────────────────
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appoi8SzEJY8in57x")

AIRTABLE_TABLES = {
    "signals_raw": "tblAFJnXToLTKeaNU",
    "projects": "tbloen0rEkHttejnC",
    "contacts": "tblPBvTBuhwlS8AnS",
    "deals": "tbl2ZkD20cf6zMxJj",
}

# ─── API Keys ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
CLAY_API_KEY = os.environ.get("CLAY_API_KEY", "")
SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
SMARTLEAD_CAMPAIGN_ID = os.environ.get("SMARTLEAD_CAMPAIGN_ID", "")
REDUCTO_API_KEY = os.environ.get("REDUCTO_API_KEY", "")
SLACK_ACCESS_TOKEN = os.environ.get("SLACK_ACCESS_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#ecas-signals")

# ─── ECAS Target Sectors ──────────────────────────────────────────────────────
# These are the UTILITIES and infrastructure developers we monitor for signals.
# When they receive capital/contracts, they hire EPCs — our actual customers.
TARGET_SECTORS = {
    "Power & Grid Infrastructure": {
        "keywords": [
            "quanta services", "mastec", "eaton", "schneider electric",
            "abb", "siemens energy", "ge vernova", "nextera energy",
            "duke energy", "southern company", "dominion energy",
            "american electric power", "vistra", "constellation energy",
            "first solar", "enphase", "sunrun", "sunnova",
            "stem inc", "fluence energy", "grid solutions",
            "aps", "salt river project", "xcel energy",
            "pacificorp", "entergy", "evergy", "dte energy",
            "sempra energy", "pge", "consolidated edison",
        ],
        "tickers": [
            "PWR", "MTZ", "ETN", "GEV", "NEE", "DUK",
            "SO", "D", "AEP", "VST", "CEG", "FSLR", "ENPH", "RUN",
            "NOVA", "STEM", "FLNC", "XEL", "ETR", "DTE", "SRE", "PCG", "ED",
        ],
        "naics_codes": ["221111", "221112", "221118", "237130", "335311", "238210"],
        "description": "Power generation, grid modernization, transmission, and clean energy",
    },
    "Defense": {
        "keywords": [
            "lockheed martin", "raytheon", "rtx", "northrop grumman",
            "general dynamics", "l3harris", "booz allen", "palantir",
            "leidos", "saic", "mantech", "parsons", "caci",
        ],
        "tickers": [
            "LMT", "RTX", "NOC", "GD", "LHX", "LDOS", "BAH",
            "PLTR", "SAIC", "MANT", "PSN", "CACI",
        ],
        "naics_codes": ["336411", "336414", "336992", "334511", "541715"],
        "description": "Defense contractors and national security",
    },
}

# ─── ICP Definition (companies we're selling TO) ─────────────────────────────
ICP = {
    "revenue_min_m": 20,    # $20M minimum
    "revenue_max_m": 300,   # $300M maximum
    "naics_codes": [
        "237130",   # Power and Communication Line and Related Structures Construction
        "238210",   # Electrical Contractors and Other Wiring Installation Contractors
        "237110",   # Water and Sewer Line and Related Structures Construction
    ],
    "titles": [
        "VP Operations", "VP Business Development", "Director of Operations",
        "President", "CEO", "Owner", "COO", "VP Preconstruction",
        "Director of Business Development", "Chief Operating Officer",
    ],
    "states": ["VA", "TX", "NC", "GA", "FL", "MD", "PA"],
    "keywords": [
        "electrical contractor", "epc contractor", "power line contractor",
        "substation contractor", "transmission contractor", "distribution contractor",
        "grid contractor", "utility contractor", "renewable contractor",
    ],
}

# ─── Alert Thresholds ─────────────────────────────────────────────────────────
ALERT_THRESHOLDS = {
    "min_politician_trades": 5,
    "min_unique_politicians": 3,
    "min_hedge_fund_positions": 3,
    "min_contract_value": 500_000,        # $500K minimum contract to track
    "min_opportunity_score": 50,
    "top_companies_count": 10,
    "politician_lookback_days": 90,
    "hedge_fund_lookback_days": 120,
    "contract_lookback_days": 90,
    "rss_lookback_hours": 48,
}

# ─── Scoring Weights ──────────────────────────────────────────────────────────
SCORING_WEIGHTS = {
    "politician_signal": 0.25,
    "hedge_fund_signal": 0.25,
    "contract_signal": 0.30,     # Contracts = direct budget signal for EPCs
    "ferc_signal": 0.10,         # FERC filings = early indicator
    "news_signal": 0.10,         # Capex announcements
}

# ─── Cascade Timeline ─────────────────────────────────────────────────────────
TIMELINE_PHASES = {
    "early_signal": {
        "description": "Politicians buying, hedge funds starting to position",
        "months_to_unlock": "6-8",
        "heat_score_range": (20, 45),
        "action": "Build sector case studies. Map target EPCs. Follow decision makers.",
    },
    "confirmed_signal": {
        "description": "Politicians + HFs aligned, contracts emerging",
        "months_to_unlock": "3-5",
        "heat_score_range": (45, 65),
        "action": "Start warm outreach. LinkedIn voice notes. 'Competitive insurance' framing.",
    },
    "imminent_unlock": {
        "description": "Large contracts awarded to utilities, EPC hiring surge",
        "months_to_unlock": "1-3",
        "heat_score_range": (65, 80),
        "action": "Direct outreach to EPC ops leaders. Show what inaction costs monthly.",
    },
    "active_spend": {
        "description": "Budgets actively deploying. RFPs being published.",
        "months_to_unlock": "0-1",
        "heat_score_range": (80, 100),
        "action": "Aggressive outreach NOW. Close before RFPs publish.",
    },
}

# ─── API Config (free public APIs — no keys needed) ──────────────────────────
API_CONFIG = {
    "house_stock_watcher_url": (
        "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com"
        "/data/all_transactions.json"
    ),
    "senate_stock_watcher_url": (
        "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com"
        "/aggregate/all_transactions.json"
    ),
    "usaspending_base_url": "https://api.usaspending.gov/api/v2",
    "sec_edgar_user_agent": os.environ.get(
        "SEC_USER_AGENT", "ECAS admin@contractmotion.com"
    ),
    "ferc_elibrary_url": "https://elibrary.ferc.gov/eLibrary/search-text",
    "ferc_search_url": "https://efts.ferc.gov/LATEST/search-index",
}

# ─── RSS Feeds ────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    {
        "name": "Utility Dive",
        "url": "https://www.utilitydive.com/feeds/news/",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "T&D World",
        "url": "https://www.tdworld.com/rss/all",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "Renewable Energy World",
        "url": "https://www.renewableenergyworld.com/feed/",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "DOE News",
        "url": "https://www.energy.gov/news/blog.rss",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "Defense News",
        "url": "https://www.defensenews.com/arc/outboundfeeds/rss/",
        "sector": "Defense",
    },
]

# ─── Claude Model ─────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"
