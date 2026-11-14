-- Audit automatique : schéma initial. Appliqué au démarrage par src/db/migrate.ts.

CREATE TABLE settings (
  key text PRIMARY KEY,
  value jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token text UNIQUE,
  status text NOT NULL CHECK (status IN ('queued','analyzing','ads','creatives','ready','failed','needs_domain')),
  domain text,
  website_url text,
  source text NOT NULL CHECK (source IN ('poller','webhook','admin')),
  contact_name text,
  contact_first_name text,
  contact_email text,
  contact_phone text,
  meeting_at timestamptz,
  analysis jsonb,
  brand jsonb,
  competitors_meta jsonb,
  insights jsonb,
  setter jsonb,
  error text,
  generations_used integer NOT NULL DEFAULT 0,
  started_at timestamptz,
  ready_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audits_domain_idx ON audits (domain, created_at DESC);
CREATE INDEX audits_status_idx ON audits (status, created_at DESC);
CREATE INDEX audits_started_idx ON audits (started_at);

-- Idempotence : call_id est la clé d'une réservation iClosed.
CREATE TABLE bookings (
  call_id text PRIMARY KEY,
  event_id text,
  audit_id uuid REFERENCES audits(id) ON DELETE SET NULL,
  booked_at timestamptz,
  meeting_at timestamptz,
  invitee_name text,
  invitee_email text,
  invitee_phone text,
  answers jsonb NOT NULL DEFAULT '[]',
  domain text,
  outcome text NOT NULL,
  source text NOT NULL,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX bookings_audit_idx ON bookings (audit_id);

-- File d'attente : FOR UPDATE SKIP LOCKED, bail renouvelé, reprise à l'expiration.
CREATE TABLE jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('audit','regenerate')),
  payload jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL CHECK (status IN ('queued','running','done','failed','cancelled')),
  run_after timestamptz NOT NULL DEFAULT now(),
  locked_by text,
  locked_until timestamptz,
  claims integer NOT NULL DEFAULT 0,
  attempts integer NOT NULL DEFAULT 0,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);
CREATE UNIQUE INDEX jobs_one_active_per_audit ON jobs (audit_id) WHERE status IN ('queued','running');
CREATE INDEX jobs_pending_idx ON jobs (run_after, created_at) WHERE status IN ('queued','running');

CREATE TABLE creatives (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  idx integer NOT NULL,
  concept text NOT NULL,
  format text NOT NULL CHECK (format IN ('4:5','9:16','1:1')),
  angle text,
  headline text,
  primary_text text,
  bullets jsonb NOT NULL DEFAULT '[]',
  cta text,
  prompt text NOT NULL,
  reference_paths jsonb NOT NULL DEFAULT '[]',
  locked boolean NOT NULL,
  status text NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','ready','failed')),
  original_file text,
  display_file text,
  blur_file text,
  thumb_file text,
  attempts integer NOT NULL DEFAULT 0,
  issues jsonb NOT NULL DEFAULT '[]',
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (audit_id, idx)
);

CREATE TABLE competitors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  ordering integer NOT NULL,
  page_id text NOT NULL,
  page_name text NOT NULL,
  ad_archive_id text,
  ad_library_url text NOT NULL,
  city text,
  distance_km integer,
  active_days integer,
  title text,
  body text NOT NULL,
  why text NOT NULL,
  logo_file text,
  image_file text,
  UNIQUE (audit_id, page_id)
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  ordering integer NOT NULL,
  title text NOT NULL,
  location text,
  image_file text NOT NULL,
  source_url text NOT NULL
);
CREATE INDEX projects_audit_idx ON projects (audit_id, ordering);

-- Seuls les noms inscrits ici sont servis ; `kind` décide de ce qui est public.
CREATE TABLE media (
  file_name text PRIMARY KEY,
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  creative_id uuid REFERENCES creatives(id) ON DELETE SET NULL,
  kind text NOT NULL CHECK (kind IN ('logo','project','competitor_image','competitor_logo','screenshot','creative_original','creative_display','creative_blur','creative_thumb')),
  path text NOT NULL,
  content_type text NOT NULL,
  bytes integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX media_audit_idx ON media (audit_id);

CREATE TABLE audit_steps (
  id bigserial PRIMARY KEY,
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  step text NOT NULL,
  status text NOT NULL,
  message text,
  meta jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_steps_audit_idx ON audit_steps (audit_id, id);

CREATE TABLE audit_costs (
  id bigserial PRIMARY KEY,
  audit_id uuid REFERENCES audits(id) ON DELETE CASCADE,
  provider text NOT NULL,
  detail text,
  quantity numeric NOT NULL DEFAULT 0,
  usd numeric,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_costs_audit_idx ON audit_costs (audit_id);

CREATE TABLE chat_sessions (
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  session_id text NOT NULL,
  messages integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (audit_id, session_id)
);

CREATE TABLE chat_daily (
  day date NOT NULL,
  audit_id uuid NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  count integer NOT NULL DEFAULT 0,
  PRIMARY KEY (day, audit_id)
);
