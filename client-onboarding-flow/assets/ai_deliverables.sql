-- Schéma minimal attendu par assets/inject_to_database.py (étape optionnelle « persister dans ta propre base »).
-- À coller dans le SQL Editor Supabase de TON projet. Adapter si ta table `profiles` s'appelle autrement.
-- Colonnes = exactement celles que le script écrit ; l'enum = VALID_TYPES du script.

create table if not exists public.ai_deliverables (
  id               uuid primary key default gen_random_uuid(),
  client_id        uuid not null references public.profiles(id) on delete cascade,
  skill_name       text not null,
  deliverable_type text not null check (deliverable_type in (
    'onboarding_form',
    'deep_search_market_awareness','deep_search_competitor_research','deep_search_psychographic',
    'competitor_ads_brief','competitor_ads_data','competitor_ads_analysis','competitor_ads_creative',
    'campaign_proposal',
    'vsl_script','vsl_strategy','vsl_docx',
    'meta_ads_copy','meta_ads_docx',
    'readme_index','other')),
  deliverable_name text not null,
  relative_path    text not null,          -- path dans le bucket Storage : {client_id}/{chemin relatif}
  file_size_bytes  bigint,
  file_extension   text,
  status           text not null default 'available',
  generated_at     timestamptz,
  updated_at       timestamptz default now(),
  unique (client_id, relative_path)        -- requis par l'upsert on_conflict du script
);

-- Bucket privé pour les fichiers (nom attendu par le script : BUCKET = "ai-deliverables")
insert into storage.buckets (id, name, public) values ('ai-deliverables', 'ai-deliverables', false)
on conflict (id) do nothing;
