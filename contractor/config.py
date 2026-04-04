"""
contractor/config.py — ICP definitions and signal configs for service contractor verticals.
Extends ECAS's main config.py pattern.
"""
import os

# Smartlead campaign IDs (to be filled after campaign creation)
CONTRACTOR_CAMPAIGN_MAP = {
    "Commercial Janitorial": os.environ.get("CAMPAIGN_JANITORIAL", ""),
    "Commercial Roofing": os.environ.get("CAMPAIGN_ROOFING", ""),
    "Pest Control": os.environ.get("CAMPAIGN_PEST_CONTROL", ""),
}

# Sending domains (warmed since 2026-03-16, ready ~2026-04-06)
CONTRACTOR_DOMAINS = [
    "getcontractmotion.com",
    "trycontractmotion.com",
    "contractmotionai.com",
    "aicontractmotion.com",
    "usecontractmotion.com",
]

# Per-vertical ICP definitions
VERTICAL_ICPS = {
    "Commercial Janitorial": {
        "description": "Independent commercial cleaning companies, 5-150 employees, B2B focused",
        "naics_codes": ["561720"],
        "employee_min": 5,
        "employee_max": 200,
        "revenue_min_m": 0.5,
        "revenue_max_m": 20,
        "target_titles": [
            "Owner", "President", "CEO", "Founder",
            "Operations Director", "General Manager", "VP Operations",
        ],
        "exclude_keywords": ["Jan-Pro", "Coverall", "ServiceMaster", "ABM", "Aramark", "Sodexo"],
        "geo_focus": ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "IL"],
        "existential_fear": "Franchise expansion (Jan-Pro/Coverall) commoditizing their territory",
        "case_study_result": "added $180K in net-new commercial contracts within 90 days",
        "apollo_keywords": ["commercial cleaning", "janitorial services", "building maintenance", "facility cleaning"],
    },
    "Commercial Roofing": {
        "description": "Commercial roofing contractors, 10-200 employees, commercial/industrial focus",
        "naics_codes": ["238160"],
        "employee_min": 10,
        "employee_max": 300,
        "revenue_min_m": 2,
        "revenue_max_m": 50,
        "target_titles": [
            "Owner", "President", "CEO", "Founder",
            "VP Sales", "Director of Business Development", "Commercial Sales Manager",
            "General Manager", "VP Operations",
        ],
        "exclude_keywords": ["residential", "Tecta America", "Nations Roof", "Weatherproofing Technologies"],
        "geo_focus": ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO"],
        "existential_fear": "Missing the post-storm replacement cycle; losing commercial bids to national chains",
        "case_study_result": "booked 14 commercial assessments in 6 weeks following a regional hail event",
        "apollo_keywords": ["commercial roofing", "roofing contractor", "commercial roof replacement", "TPO roofing", "EPDM roofing"],
    },
    "Pest Control": {
        "description": "Independent pest control operators, 5-150 employees, commercial accounts focus",
        "naics_codes": ["561710"],
        "employee_min": 5,
        "employee_max": 200,
        "revenue_min_m": 0.5,
        "revenue_max_m": 15,
        "target_titles": [
            "Owner", "President", "CEO", "Founder",
            "Operations Manager", "Branch Manager", "General Manager",
            "Commercial Sales Manager",
        ],
        "exclude_keywords": ["Rollins", "Rentokil", "Terminix", "ServiceMaster", "Orkin", "Western Pest"],
        "geo_focus": ["TX", "FL", "GA", "NC", "SC", "TN", "AL", "MS"],
        "existential_fear": "Rollins/Rentokil buying their local competitors and underpricing to lock in commercial contracts",
        "case_study_result": "grew commercial recurring revenue 40% in 90 days without adding routes",
        "apollo_keywords": ["pest control", "exterminator", "commercial pest", "integrated pest management", "rodent control"],
    },
}

# Signal weights for service contractor verticals (ColdIQ multi-signal framework)
CONTRACTOR_SIGNAL_WEIGHTS = {
    # Tier 1 - Hot (50-100 pts)
    "commercial_permit_pulled": 65,        # Target building pulled a permit — active spend
    "hail_event_large": 80,               # Roofing: hail > 1.5" — replacement wave incoming
    "hail_event_medium": 50,              # Roofing: hail 0.75-1.5"
    "franchise_new_territory": 70,        # Jan-Pro/Coverall expanding nearby — existential trigger
    "competitor_acquisition": 60,         # Rollins buying local competitor — fear trigger
    "fm_job_change": 75,                  # New FM/Building Manager hired at target account
    "contract_renewal_window": 55,        # 90-day window before typical annual contract renewal
    # Tier 2 - Warm (20-49 pts)
    "fm_job_posting": 40,                 # Company hiring FM = pain with current vendor
    "negative_review_competitor": 35,     # G2/Yelp bad review of current pest/cleaning vendor
    "hiring_spree": 35,                   # Growing headcount = more facilities to service
    "new_location_opened": 45,            # New office/facility = new service contract needed
    "commercial_building_sold": 40,       # New ownership = new vendor decisions
    "linkedin_content_engagement": 25,    # Engaged with ContractMotion/relevant content
    "industry_association_member": 20,    # BSCAI/NPMA member = professional operator
    # Tier 3 - Cool (5-19 pts)
    "company_news": 15,
    "email_open": 5,
    "website_visit": 10,
}

# NOAA Storm Events API config
NOAA_API_CONFIG = {
    "base_url": "https://www.ncdc.noaa.gov/stormevents/csv",
    "hail_threshold_large_inches": 1.5,   # Major hail → high priority
    "hail_threshold_medium_inches": 0.75, # Medium hail → medium priority
    "lookback_days": 14,
    "target_states": ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO", "KS", "OK"],
}

# Permit scraper config (city open data APIs)
PERMIT_SOURCES = [
    {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/3syk-w9eu.json", "type": "socrata"},
    {"city": "Dallas, TX", "url": "https://www.dallasopendata.com/resource/itp2-kpxj.json", "type": "socrata"},
    {"city": "Charlotte, NC", "url": "https://data.charlottenc.gov/resource/rbp5-htyk.json", "type": "socrata"},
    {"city": "Atlanta, GA", "url": "https://opendata.atlantaga.gov/resource/jcnz-gpd5.json", "type": "socrata"},
]
PERMIT_MIN_VALUE = 50_000  # Only track permits > $50K (commercial scale)
PERMIT_TYPES = ["commercial", "office", "retail", "industrial", "warehouse", "restaurant"]
