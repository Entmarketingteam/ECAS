-- Foretrust Verified Lead Gate
-- 
-- Pure verified lead gate scaffold: lead_raw -> lead_oracle/evidence -> lead_verdicts -> lead_published/pass queue
-- 
-- This migration adds the verification pipeline tables.

-- Lead Oracle Evidence table (stores verification evidence)
CREATE TABLE IF NOT EXISTS ft_lead_oracle_evidence (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID NOT NULL REFERENCES ft_leads(id) ON DELETE CASCADE,
  oracle_type VARCHAR(50) NOT NULL CHECK (oracle_type IN ('icp_match', 'intent_signal', 'contact_validation', 'domain_verification')),
  evidence_data JSONB NOT NULL DEFAULT '{}',
  confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
  is_verifiable BOOLEAN NOT NULL DEFAULT TRUE,
  verified_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lead Verdicts table (stores verification decisions)
CREATE TABLE IF NOT EXISTS ft_lead_verdicts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID NOT NULL UNIQUE REFERENCES ft_leads(id) ON DELETE CASCADE,
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verification_reason TEXT,
  evidence_summary JSONB DEFAULT '[]',
  needs_review BOOLEAN NOT NULL DEFAULT FALSE,
  reviewed_by UUID REFERENCES ft_users(id),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lead Published/Pass Queue (verified leads ready for publication)
CREATE TABLE IF NOT EXISTS ft_lead_published_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID NOT NULL UNIQUE REFERENCES ft_leads(id) ON DELETE CASCADE,
  verdict_id UUID NOT NULL UNIQUE REFERENCES ft_lead_verdicts(id) ON DELETE CASCADE,
  publish_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (publish_status IN ('pending', 'published', 'failed')),
  published_at TIMESTAMP WITH TIME ZONE,
  publish_error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ft_lead_oracle_evidence_lead ON ft_lead_oracle_evidence(lead_id);
CREATE INDEX IF NOT EXISTS idx_ft_lead_oracle_evidence_type ON ft_lead_oracle_evidence(oracle_type);
CREATE INDEX IF NOT EXISTS idx_ft_lead_oracle_evidence_verified ON ft_lead_oracle_evidence(verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_ft_lead_verdicts_verified ON ft_lead_verdicts(is_verified);
CREATE INDEX IF NOT EXISTS idx_ft_lead_verdicts_review ON ft_lead_verdicts(needs_review);
CREATE INDEX IF NOT EXISTS idx_ft_lead_published_queue_status ON ft_lead_published_queue(publish_status);
CREATE INDEX IF NOT EXISTS idx_ft_lead_published_queue_pending ON ft_lead_published_queue(created_at) WHERE publish_status = 'pending';

-- Trigger to auto-update timestamps
CREATE TRIGGER update_ft_lead_oracle_evidence_updated_at
  BEFORE UPDATE ON ft_lead_oracle_evidence
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ft_lead_verdicts_updated_at
  BEFORE UPDATE ON ft_lead_verdicts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Set up RLS for the new tables
ALTER TABLE ft_lead_oracle_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE ft_lead_verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ft_lead_published_queue ENABLE ROW LEVEL SECURITY;

-- RLS Policies (using existing get_user_org_id() helper function)
CREATE POLICY "Users can access lead oracle evidence" ON ft_lead_oracle_evidence
  FOR ALL USING (EXISTS (
    SELECT 1 FROM ft_leads l
    WHERE l.id = lead_id AND l.organization_id = get_user_org_id()
  ));

CREATE POLICY "Users can access lead verdicts" ON ft_lead_verdicts
  FOR ALL USING (EXISTS (
    SELECT 1 FROM ft_leads l
    WHERE l.id = lead_id AND l.organization_id = get_user_org_id()
  ));

CREATE POLICY "Users can access published queue" ON ft_lead_published_queue
  FOR ALL USING (EXISTS (
    SELECT 1 FROM ft_leads l
    WHERE l.id = lead_id AND l.organization_id = get_user_org_id()
  ));

COMMENT ON TABLE ft_lead_oracle_evidence IS 'Stores verification evidence for leads from various oracle sources';
COMMENT ON TABLE ft_lead_verdicts IS 'Verification decisions and review status for leads';
COMMENT ON TABLE ft_lead_published_queue IS 'Queue for verified leads ready for publication or next processing steps';