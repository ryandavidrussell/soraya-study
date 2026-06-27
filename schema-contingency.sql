-- schema_contingency.sql
-- Soraya Study · Kaleidoworks
--
-- Adds the contingency_events table for the fade-property auditor
-- (contingency_audit.py -> contingency_hook.py -> db.record_contingency_event).
--
-- Run once in the Supabase SQL editor for the study project, AFTER the main
-- schema.sql. Mirrors the other study tables: INSERT-only under RLS, no SELECT
-- policy, so the Space can write contingency rows but cannot read participant
-- data back. Exports and withdrawals use the offline key (study_admin.py).
--
-- Safe to re-run: create ... if not exists, and the policy is dropped before
-- re-create so a second run does not error on an existing policy.

create table if not exists contingency_events (
    id                    uuid primary key,
    participant_id        text not null,
    session_id            text not null,
    turn_number           int not null,
    verdict               text not null,  -- CONTINGENT_OK | FADE_FAILURE | HELD_LOW | NO_SIGNAL_NA
    prev_mode             text,
    curr_mode             text,
    prev_rank             int,
    curr_rank             int,
    band_prev             text,
    band_curr             text,
    competence_signal     boolean,
    signal_attempt_token  boolean,
    signal_success_marker boolean,
    proxy_warning         text,
    note                  text,
    schema_version        text,
    recorded_at           timestamptz not null
);

-- Row Level Security: write-only from the Space's anon key.
alter table contingency_events enable row level security;

-- INSERT-only policy for the anon role. Dropped first so re-running this
-- file is idempotent rather than erroring on a duplicate policy name.
drop policy if exists "anon insert contingency" on contingency_events;
create policy "anon insert contingency"
    on contingency_events
    for insert
    to anon
    with check (true);

-- NO select policy is defined on purpose: the Space cannot read participant
-- rows. Reads happen only via the offline service key in study_admin.py.

-- Add contingency_events to study_admin.py's _fetch table lists so exports
-- and participant-deletion sweeps include it (it carries participant_id).
