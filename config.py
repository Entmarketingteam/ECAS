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

# Maps sector (scope_summary in Airtable projects) → Smartlead campaign ID.
# Contacts are auto-routed at enrollment time based on their parent project's sector.
# Power & Grid is the default fallback for any unmapped sector.
SECTOR_CAMPAIGN_MAP: dict[str, str] = {
    "Power & Grid Infrastructure":           "3005694",
    "Nuclear & Critical Minerals":           "3005694",  # routes to Power & Grid (closest fit)
    "Data Center & AI Infrastructure":       "3040599",
    "Water & Wastewater Infrastructure":     "3040600",
    "Water & Wastewater":                    "3040600",  # alias
    "Industrial & Manufacturing Facilities": "3040601",
    "Defense":                               "3095136",
    "Defense & Federal Infrastructure":      "3095136",  # alias
    # Drone/DFR vertical — B2G track targeting drone vendor BD/sales teams
    # Campaign created 2026-03-30 — 6 sequences live
    "Drone & Public Safety Technology":      "3103531",
}
FINDYMAIL_API_KEY = os.environ.get("FINDYMAIL_API_KEY", "")

# Google Maps / RapidAPI
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

# Blitz — domain → decision-maker contacts
BLITZ_API_KEY = os.environ.get("BLITZ_API_KEY", "")
BLITZ_BASE_URL = os.environ.get("BLITZ_BASE_URL", "https://api.useblitz.com")

# Prospeo — domain search fallback
PROSPEO_API_KEY = os.environ.get("PROSPEO_API_KEY", "")

# MillionVerifier — email validation
MILLIONVERIFIER_API_KEY = os.environ.get("MILLIONVERIFIER_API_KEY", "")

# Google Maps target queries mapped to ECAS sectors
GMAPS_QUERIES: list[dict] = [
    {"query": "electrical contractor",       "sector": "Power & Grid Infrastructure"},
    {"query": "solar contractor",            "sector": "Power & Grid Infrastructure"},
    {"query": "data center construction",    "sector": "Data Center & AI Infrastructure"},
    {"query": "general contractor",          "sector": "Industrial & Manufacturing Facilities"},
    {"query": "mechanical contractor",       "sector": "Industrial & Manufacturing Facilities"},
    {"query": "water treatment contractor",  "sector": "Water & Wastewater Infrastructure"},
    {"query": "engineering firm",            "sector": "Power & Grid Infrastructure"},
    {"query": "construction company",        "sector": "Industrial & Manufacturing Facilities"},
]

SLACK_ACCESS_TOKEN = os.environ.get("SLACK_ACCESS_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#ecas-signals")
# EIA Open Data API — free, register at https://www.eia.gov/opendata/register.php
# Falls back to "DEMO_KEY" (rate-limited) if not set
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")
# New Signal Source API Keys (all free registration)
SAM_GOV_API_KEY = os.environ.get("SAM_GOV_API_KEY", "")       # sam.gov
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")          # api.census.gov
BLS_API_KEY = os.environ.get("BLS_API_KEY", "")                # api.bls.gov
CONGRESS_API_KEY = os.environ.get("CONGRESS_API_KEY", "")      # api.congress.gov

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
            # AI data center power layer — upstream demand driver for EPCs
            "vertiv", "generate capital", "on-site power", "modular power",
            "data center cooling", "grid-constrained", "hyperscaler power",
        ],
        "tickers": [
            "PWR", "MTZ", "ETN", "GEV", "NEE", "DUK",
            "SO", "D", "AEP", "VST", "CEG", "FSLR", "ENPH", "RUN",
            "NOVA", "STEM", "FLNC", "XEL", "ETR", "DTE", "SRE", "PCG", "ED",
            # Vertiv: modular power+cooling for AI DCs — grid-constrained markets
            "VRT",
            # Hyperscalers: capex hikes here = downstream EPC demand signal
            "MSFT", "AMZN", "GOOGL", "META",
            # Energy infrastructure — pipelines/midstream signal capital flowing into grid-adjacent sectors
            "WMB", "KMI", "LNG", "CVX", "DTM", "AM",
            # AI data center power demand — Bitcoin miners + HPC = grid load signal
            "WULF", "CORZ", "APLD",
        ],
        "naics_codes": ["221111", "221112", "221118", "237130", "335311", "238210"],
        "description": "Power generation, grid modernization, transmission, clean energy, and AI data-center power infrastructure",
    },
    "Defense": {
        "keywords": [
            "lockheed martin", "raytheon", "rtx", "northrop grumman",
            "general dynamics", "l3harris", "booz allen", "palantir",
            "leidos", "saic", "mantech", "parsons", "caci",
            # UAV/Counter-UAS layer — active DoD award signals
            "kratos defense", "aerovironment", "counter-uas", "c-uas",
            "unmanned aerial", "drone defense", "loitering munition",
            # Public safety / enterprise surveillance
            "axon enterprise", "body camera", "public safety tech",
        ],
        "tickers": [
            "LMT", "RTX", "NOC", "GD", "LHX", "LDOS", "BAH",
            "PLTR", "SAIC", "MANT", "PSN", "CACI",
            # UAV/Counter-UAS — active DoD production awards as of March 2026
            "KTOS", "AVAV", "RCAT",
            # Public safety tech with capex expansion signal
            "AXON",
            # Electronic warfare + maritime defense — SHIELD IDIQ signal companies
            "HII", "LDOS", "BWXT", "VEC",
        ],
        "naics_codes": ["336411", "336414", "336992", "334511", "541715"],
        "description": "Defense contractors, national security, UAV/Counter-UAS, and public safety technology",
    },
    "Nuclear & Critical Minerals": {
        "keywords": [
            "small modular reactor", "smr", "nuclear power plant", "advanced nuclear",
            "uranium enrichment", "rare earth", "critical minerals",
            "oklo", "last energy", "x-energy", "nuscale", "kairos power",
            "uranium mining", "nuclear fuel", "nuclear ppa",
            "cameco", "energy fuels", "uranium energy", "mp materials",
            "hyperscaler nuclear", "data center nuclear", "oracle nuclear",
        ],
        "tickers": [
            # Uranium/fuel supply chain — $2.7B federal grants, hyperscaler PPAs
            "UEC", "CCJ", "UUUU",
            # Rare earths — defense and EV supply chain
            "MP",
            # AI networking/custom silicon — proxy for hyperscaler capex cycle
            "AVGO", "MRVL",
            # Enterprise AI workflow — large $1M+ ACV deals signal macro spend
            "NOW",
        ],
        "naics_codes": ["212291", "212299", "221113", "325180", "331410"],
        "description": "Nuclear power infrastructure, SMR development, uranium supply chain, and critical minerals for AI/defense buildout",
    },
    "Data Center & AI Infrastructure": {
        "keywords": [
            "hyperscaler", "data center campus", "ai campus", "colocation facility",
            "microsoft data center", "amazon data center", "google data center",
            "meta data center", "nvidia data center", "data center power",
            "on-site generation", "modular power", "grid-constrained data center",
            "critical facility", "tier 3 data center", "tier 4 data center",
            "campus power", "hyperscale campus", "digital realty", "equinix",
            "coresite", "cyrusone", "iron mountain dc", "data center construction",
            "data center epc", "dc campus substation", "campus 33kv", "campus 138kv",
        ],
        "tickers": [
            # Hyperscalers — capex hike = downstream EPC demand
            "MSFT", "AMZN", "GOOGL", "META", "ORCL",
            # GPU/AI infra — supply signals for power demand
            "NVDA", "AMD",
            # Data center REITs
            "DLR", "EQIX", "CONE", "QTS",
            # Power/cooling for DCs
            "VRT", "SMCI", "ANET",
            # Crypto miners (repurposing grid capacity = EPC opportunity)
            "WULF", "CORZ", "APLD", "MARA",
        ],
        "naics_codes": ["518210", "236220", "237130", "238210", "541513"],
        "description": "Hyperscaler and colocation data center campus construction requiring 100–1000 MW power infrastructure. Fastest-growing EPC demand segment in 2025-2027.",
    },
    "Water & Wastewater Infrastructure": {
        "keywords": [
            "water treatment plant", "wastewater treatment", "water infrastructure",
            "cwsrf", "dwsrf", "state revolving fund", "clean water act",
            "water system upgrade", "water main replacement", "lead service line",
            "water resilience", "desalination plant", "water reclamation",
            "municipal water", "stormwater", "combined sewer overflow",
            "iija water", "bipartisan infrastructure water",
            "american water works", "veolia water", "aecom water",
            "jacobs water", "black and veatch water", "wsatco",
        ],
        "tickers": [
            # Water utilities — capex = EPC spend
            "AWK", "WTR", "MSEX", "CWCO", "YORW",
            # Water tech/treatment
            "XYL", "XYLEM", "PNR", "FELE", "REXNORD",
            # Infrastructure — overlaps with power EPCs
            "PWR", "MTZ",
        ],
        "naics_codes": ["221310", "221320", "237110", "237120", "562212"],
        "description": "Municipal water and wastewater infrastructure upgrades funded by IIJA/BIL state revolving funds. $50B+ federal spend through 2026.",
    },
    # ── Drone & Public Safety Technology ─────────────────────────────────────
    # B2G track: we monitor MUNICIPALITIES for DFR buying intent.
    # We sell those signals to drone vendors (BRINC, Skydio, Percepto, Fotokite, Axon Air).
    # Signals: SAM.gov UAS RFIs, FEMA/COPS grants, city council minutes, USASpending drone awards.
    "Drone & Public Safety Technology": {
        "keywords": [
            # DFR program signals
            "drone as first responder", "dfr program", "autonomous drone dispatch",
            "police drone program", "public safety drone", "drone dock",
            "drone nest", "drone in a box", "bvlos waiver",
            # RTCC and surveillance infrastructure
            "real-time crime center", "rtcc", "gunshot detection", "shotspotter",
            "aerial surveillance", "persistent aerial", "drone overwatch",
            # Vendor-specific (signals a municipality already bought or is evaluating)
            "brinc", "skydio", "fotokite", "percepto", "axon air", "dedrone",
            "american robotics", "droneup",
            # Procurement + compliance signals
            "ndaa compliant drone", "american-made uas", "section 848",
            "uas program", "unmanned aircraft system police",
            "public safety uas", "aerial first responder",
            # Grant programs that fund DFR purchases
            "cops technology grant", "bsir grant", "edward byrne jag",
            "public safety technology grant",
        ],
        "tickers": [
            # Publicly traded drone/public safety tech companies
            "AXON",   # Axon Enterprise — body cams, RTCC, Dedrone
            "KTOS",   # Kratos — defense UAS, public safety adjacency
            "AVAV",   # AeroVironment — UAS manufacturer
            "RCAT",   # Red Cat Holdings — public safety drones (NDAA-compliant)
            # Gunshot detection / RTCC
            "SST",    # SoundThinking (ShotSpotter)
            # Public safety tech
            "MSI",    # Motorola Solutions — RTCC, CAD integration
        ],
        "naics_codes": [
            "922120",  # Police Protection
            "922160",  # Fire Protection
            "922190",  # Other Justice, Public Order, Safety
            "336411",  # Aircraft Manufacturing (drone makers)
            "334511",  # Search, Detection, Navigation instruments
        ],
        "description": "Municipal DFR program procurement signals — SAM.gov UAS RFIs, FEMA/COPS grant awards, BVLOS waivers, city council DFR resolutions. Sold to drone vendor BD teams.",
    },
    "Industrial & Manufacturing Facilities": {
        "keywords": [
            "semiconductor fab", "chips act", "tsmc", "intel fab", "samsung fab",
            "micron fab", "ev battery factory", "gigafactory", "battery gigafactory",
            "lng export terminal", "natural gas liquefaction", "lng facility",
            "hydrogen plant", "green hydrogen", "ammonia facility",
            "industrial campus", "manufacturing expansion", "greenfield facility",
            "freeport lng", "sabine pass", "calcasieu pass",
            "ford ev plant", "gm ev plant", "rivian factory",
            "industrial power", "heavy industrial epc", "process plant",
            "refinery upgrade", "petrochemical expansion",
        ],
        "tickers": [
            # Semis — fab construction = massive power/civil EPC contracts
            "TSM", "INTC", "SSNLF", "MU", "AMAT",
            # EV/battery — gigafactory = 500+ MW demand
            "TSLA", "F", "GM", "RIVN", "QS",
            # LNG — terminal = big EPC
            "LNG", "CQP", "NEXT", "CVX", "XOM",
            # Industrial gases / hydrogen
            "LIN", "APD", "CE",
        ],
        "naics_codes": ["336390", "311312", "325193", "324110", "333249"],
        "description": "CHIPS Act semiconductor fabs, EV gigafactories, LNG export terminals, and hydrogen/ammonia facilities — all requiring 500MW+ power infrastructure built by EPCs.",
    },
}

# ─── ICP Definition (companies we're selling TO) ─────────────────────────────
# Primary ICP: mid-tier EPC contractors ($20M–$300M) in infrastructure verticals
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

# B2G ICP: drone/DFR vendors we sell municipal buying signals TO
ICP_DRONE_VENDORS = {
    "revenue_min_m": 2,      # includes well-funded startups
    "revenue_max_m": 1000,   # up to Axon/Motorola scale
    "naics_codes": [
        "336411",   # Aircraft Manufacturing (drone OEMs)
        "334511",   # Search/Detection/Navigation instruments
        "511210",   # Software Publishers (drone software platforms)
        "561621",   # Security Systems Services
        "922120",   # Police Protection (for agency-side contacts)
    ],
    "titles": [
        "VP of Sales", "VP of Government Sales", "Director of Business Development",
        "Head of Public Safety Sales", "Director of Federal and Government Programs",
        "Chief Revenue Officer", "VP of Revenue", "Head of Sales",
        "State and Local Government Sales", "Director of Partnerships",
        "VP of Public Safety", "Head of Law Enforcement Sales",
    ],
    "target_companies": [
        "BRINC", "Skydio", "Percepto", "Fotokite", "Axon Enterprise",
        "American Robotics", "DroneUp", "Shield AI", "Red Cat Holdings",
        "Motorola Solutions", "SoundThinking", "Dedrone",
        "Joby Aviation", "Valqari", "Ondas Holdings",
    ],
    "keywords": [
        "drone as first responder", "public safety drone", "dfr",
        "autonomous drone", "drone-in-a-box", "police drone",
        "ndaa compliant drone", "government drone sales",
        "public safety technology", "law enforcement drone",
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
    "contract_signal": 0.25,     # Contracts = direct budget signal for EPCs
    "ferc_signal": 0.10,         # FERC filings = early indicator
    "news_signal": 0.05,         # RSS news signals
    "earnings_signal": 0.10,     # Earnings call transcripts — capex hike, SMR/nuclear, grid language
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
    # Quiver Quantitative — replaced defunct S3 Stock Watcher endpoints (403 as of 2026-03)
    # Free tier, no API key, returns 1000 most recent trades across both chambers
    "quiver_congress_url": "https://api.quiverquant.com/beta/live/congresstrading",
    # Legacy (kept for reference, both return 403)
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
    # Texas RRC drilling permits — 614 new permits in Feb 2026 alone.
    # High permit volume = upstream O&G activity = power infrastructure demand signal.
    # TODO: wire direct API/scrape of https://www.rrc.texas.gov/resource-center/research/data-sets-available-for-download/
    # {
    #     "name": "Texas RRC",
    #     "url": "https://www.rrc.texas.gov/resource-center/research/data-sets-available-for-download/",
    #     "sector": "Power & Grid Infrastructure",
    # },

    # ── PPA / Renewable Finance feeds (added 2026-03-13) ──────────────────────
    # These cover PPA announcements, project finance closings, and utility-scale
    # project news — all tier-1 EPC demand signals (PPA signed → plant to be built).
    {
        "name": "PV Magazine USA",
        "url": "https://www.pv-magazine-usa.com/feed/",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "POWER Magazine",
        "url": "https://www.powermag.com/feed/",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "Energy Monitor",
        "url": "https://www.energymonitor.ai/feed/",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "Canary Media",
        "url": "https://www.canarymedia.com/rss",
        "sector": "Power & Grid Infrastructure",
    },

    # ── Nuclear / Critical Minerals (added 2026-03-13) ────────────────────────
    # NEI covers SMR deals, nuclear PPAs, and DOE grant announcements.
    {
        "name": "Nuclear Energy Institute",
        "url": "https://www.nei.org/rss/news",
        "sector": "Nuclear & Critical Minerals",
    },

    # ── State PUC / Utility Regulation coverage (added 2026-03-13) ───────────
    # These outlets cover rate case filings, IRP approvals, and utility capex plans
    # in high-activity EPC markets (VA, TX). Rate case approval → capex unlock.
    {
        "name": "Texas Tribune Energy",
        "url": "https://www.texastribune.org/sections/energy-environment/rss.xml",
        "sector": "Power & Grid Infrastructure",
    },
    {
        "name": "Virginia Mercury",
        "url": "https://virginiamercury.com/feed/",
        "sector": "Power & Grid Infrastructure",
    },

    # ── Data Center & AI Infrastructure (added 2026-03-15) ───────────────────
    # Covers hyperscaler campus builds, colocation expansions, and DC power
    # infrastructure — all driving 100–1000 MW EPC substation demand.
    {
        "name": "Data Center Dynamics",
        "url": "https://www.datacenterdynamics.com/en/rss/",
        "sector": "Data Center & AI Infrastructure",
    },
    {
        "name": "Data Center Frontier",
        "url": "https://datacenterfrontier.com/feed/",
        "sector": "Data Center & AI Infrastructure",
    },
    {
        "name": "The Register DC",
        "url": "https://www.theregister.com/data_centre/feed.atom",
        "sector": "Data Center & AI Infrastructure",
    },

    # ── Water & Wastewater Infrastructure (added 2026-03-15) ─────────────────
    # IIJA/BIL state revolving fund disbursements — $50B+ through 2026.
    # Water EPCs and power EPCs share contractor pools in most target states.
    {
        "name": "Water World",
        "url": "https://www.waterworld.com/rss/all",
        "sector": "Water & Wastewater Infrastructure",
    },
    {
        "name": "Water Finance & Management",
        "url": "https://waterfm.com/feed/",
        "sector": "Water & Wastewater Infrastructure",
    },

    # ── Industrial & Manufacturing Facilities (added 2026-03-15) ─────────────
    # CHIPS Act fabs, EV gigafactories, LNG terminals, hydrogen plants —
    # all 500MW+ power builds contracted to EPCs.
    {
        "name": "Chemical Engineering",
        "url": "https://www.chemengonline.com/feed/",
        "sector": "Industrial & Manufacturing Facilities",
    },
    {
        "name": "LNG Industry",
        "url": "https://www.lngindustry.com/rss/",
        "sector": "Industrial & Manufacturing Facilities",
    },
    {
        "name": "Semiconductor Engineering",
        "url": "https://semiengineering.com/feed/",
        "sector": "Industrial & Manufacturing Facilities",
    },

    # ── Drone & Public Safety Technology (added 2026-03-30) ──────────────────
    # Monitor municipal DFR buying signals — grant awards, program announcements,
    # technology procurement notices. Sold to drone vendor BD teams.
    {
        "name": "Police1",
        "url": "https://www.police1.com/rss/all/",
        "sector": "Drone & Public Safety Technology",
    },
    {
        "name": "Government Technology",
        "url": "https://www.govtech.com/rss/all",
        "sector": "Drone & Public Safety Technology",
    },
    {
        "name": "Urgent Communications (IWCE)",
        "url": "https://urgentcomm.com/feed/",
        "sector": "Drone & Public Safety Technology",
    },
    {
        "name": "Commercial UAV News",
        "url": "https://www.commercialuavnews.com/feed",
        "sector": "Drone & Public Safety Technology",
    },
    {
        "name": "Dronelife",
        "url": "https://dronelife.com/feed/",
        "sector": "Drone & Public Safety Technology",
    },
]

# ─── Claude Model ─────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"

# ─── External Watchlists (reference only — not polled directly) ───────────────
# Simply Wall Street export (March 2026, 1132 companies) — ~/Downloads/Simply Wall Street...
# Key energy tickers not in TARGET_SECTORS above: WMB, KMI, LNG, CVX, DTM, AM, WULF, CORZ, APLD
# Use for LinkedIn outreach to energy/defense sector capital allocators.
#
# MDA SHIELD IDIQ awardees (Dec 2025, 1079 companies) — use seed_shield_awardees.py
# 399 EPC-adjacent companies with confirmed DoD contracts. Run seeder to populate Airtable projects.
#
# EnCap Investments team data — ~/Downloads/Private Equity/encapinvestments*.csv
# PE fund focused on O&G. Portfolio companies = upstream capital signal for grid EPC demand.
# Texas RRC Feb 2026: 614 new drill permits = active upstream O&G → downstream power EPC demand.
