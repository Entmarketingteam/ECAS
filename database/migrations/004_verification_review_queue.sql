-- Migration: verification_review_queue
-- Human review queue for leads that don't pass automated verification

CREATE TABLE IF NOT EXISTS verification_review_queue (
    id                  BIGSERIAL PRIMARY KEY,
    company_name        TEXT NOT NULL,
    domain              TEXT NOT NULL DEFAULT '',
    sector              TEXT NOT NULL DEFAULT '',
    state               TEXT NOT NULL DEFAULT '',
    confidence_score    INT NOT NULL DEFAULT 0,
    final_route         TEXT NOT NULL DEFAULT 'REVIEW',  -- AUTO | REVIEW | HOLD
    flags               JSONB,                           -- array of flag strings
    content_draft       TEXT,                            -- generated content awaiting approval
    reviewed            BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by         TEXT,
    reviewed_at         TIMESTAMPTZ,
    reviewer_notes      TEXT,
    approved            BOOLEAN,                         -- null=pending, true=approved, false=rejected
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (company_name, domain)
);

CREATE INDEX IF NOT EXISTS idx_vrq_route     ON verification_review_queue (final_route);
CREATE INDEX IF NOT EXISTS idx_vrq_reviewed  ON verification_review_queue (reviewed);
CREATE INDEX IF NOT EXISTS idx_vrq_approved  ON verification_review_queue (approved);
CREATE INDEX IF NOT EXISTS idx_vrq_created   ON verification_review_queue (created_at DESC);

COMMENT ON TABLE verification_review_queue IS
    'Human review queue for leads that failed automated verification checks. '
    'Reviewer approves or rejects, sets reviewed=true, approved=true/false.';
