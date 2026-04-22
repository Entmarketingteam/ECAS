-- Google Maps discovered companies
create table if not exists gmaps_companies (
  id               uuid primary key default gen_random_uuid(),
  place_id         text unique not null,
  name             text,
  address          text,
  phone            text,
  website_domain   text,
  rating           numeric(3,1),
  total_reviews    integer,
  zip_code         text,
  state            text,
  query            text,
  sector           text,
  created_at       timestamptz default now(),
  enriched_at      timestamptz,
  enrichment_status text default 'pending'
);

create index if not exists gmaps_companies_status_idx on gmaps_companies(enrichment_status);
create index if not exists gmaps_companies_zip_idx on gmaps_companies(zip_code);

-- Decision-maker contacts found via Blitz/Prospeo enrichment
create table if not exists gmaps_contacts (
  id               uuid primary key default gen_random_uuid(),
  place_id         text references gmaps_companies(place_id),
  company_name     text,
  website_domain   text,
  first_name       text,
  last_name        text,
  title            text,
  email            text,
  email_quality    text,
  linkedin_url     text,
  source           text,
  created_at       timestamptz default now(),
  enrolled_at      timestamptz,
  smartlead_campaign_id text
);

create index if not exists gmaps_contacts_enrolled_idx on gmaps_contacts(enrolled_at);
create index if not exists gmaps_contacts_quality_idx on gmaps_contacts(email_quality);

-- Enrollment event log (audit trail)
create table if not exists enrollment_log (
  id               uuid primary key default gen_random_uuid(),
  contact_email    text not null,
  smartlead_campaign_id text,
  source           text,
  enrolled_at      timestamptz default now(),
  lead_data        jsonb
);
