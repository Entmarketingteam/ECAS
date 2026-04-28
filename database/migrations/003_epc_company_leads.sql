-- Migration: epc_company_leads
-- Free-source EPC lead discovery (WEFTEC, AWWA, CWSRF, AFCOM, 7x24, etc.)

CREATE TABLE IF NOT EXISTS epc_company_leads (
    id                  BIGSERIAL PRIMARY KEY,
    company_name        TEXT NOT NULL,
    domain              TEXT NOT NULL DEFAULT '',
    source              TEXT NOT NULL,         -- e.g. 'WEFTEC', 'AWWA-TX', 'USASpending-NAICS-237110'
    sector              TEXT NOT NULL,         -- 'Water & Wastewater' | 'Data Center & AI Infrastructure' | 'Power & Grid'
    state               TEXT NOT NULL DEFAULT '',
    city                TEXT NOT NULL DEFAULT '',
    raw_data            JSONB,
    scraped_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enrolled_smartlead  BOOLEAN NOT NULL DEFAULT FALSE,
    smartlead_campaign_id BIGINT,
    smartlead_lead_id   BIGINT,
    enrolled_at         TIMESTAMPTZ,
    notes               TEXT,
    UNIQUE (domain, source)                    -- dedup: same company from same source once
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_epc_leads_sector    ON epc_company_leads (sector);
CREATE INDEX IF NOT EXISTS idx_epc_leads_state     ON epc_company_leads (state);
CREATE INDEX IF NOT EXISTS idx_epc_leads_enrolled  ON epc_company_leads (enrolled_smartlead);
CREATE INDEX IF NOT EXISTS idx_epc_leads_source    ON epc_company_leads (source);
CREATE INDEX IF NOT EXISTS idx_epc_leads_scraped   ON epc_company_leads (scraped_at DESC);

COMMENT ON TABLE epc_company_leads IS
    'EPC contractor leads sourced from free public directories, associations, '
    'conference exhibitor lists, government databases. No paid API keys required.';
