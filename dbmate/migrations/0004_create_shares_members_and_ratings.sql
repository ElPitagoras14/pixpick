-- migrate:up

-- The token and the access it once granted are two different things (D1):
-- the token governs who can *enter*, `album_members` below governs who
-- *has access*. Revoked rows are kept, never deleted, so a token can never
-- be reused and so "revoked" stays distinguishable from "never existed" in
-- the server's own records, even though the two answer identically to
-- whoever presents the token.
--
-- Stored as plain text, unlike a session token: the owner SHALL be able to
-- fetch the same live link back on demand (album-sharing spec), which a
-- one-way hash would make impossible. Its blast radius if the database
-- leaked is also far smaller than a session's -- read access and rating on
-- one album, never an account takeover -- so the asymmetry with sessions
-- (session-management spec, hashed) is deliberate, not an oversight.
create table share_tokens (
  id uuid primary key default gen_random_uuid(),
  album_id uuid not null references albums (id) on delete cascade,
  token text not null unique,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Supports both "does this album already have a live link" (D2: regenerate
-- revokes the current one first) and looking up an album's own history of
-- links, neither of which should be a sequential scan.
create index share_tokens_album_id_idx on share_tokens (album_id);

create trigger set_share_tokens_updated_at
before update on share_tokens
for each row execute function set_updated_at();

-- A relation between a person and an album, with its own lifecycle --
-- never a consequence of the token above. This is what makes revoking a
-- link harmless to people who already entered (D1).
create table album_members (
  album_id uuid not null references albums (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (album_id, user_id)
);

-- The primary key already indexes (album_id, user_id) in that order; this
-- covers the other direction -- "every album a person is a member of" --
-- which the album list query (D9) runs on every request.
create index album_members_user_id_idx on album_members (user_id);

create trigger set_album_members_updated_at
before update on album_members
for each row execute function set_updated_at();

-- One rating per photo per person, enforced by the schema and not by the
-- application (photo-rating spec): the uniqueness is what makes the
-- upsert in a single statement (D3) possible in the first place.
create table photo_ratings (
  id uuid primary key default gen_random_uuid(),
  photo_id uuid not null references photos (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  approved boolean not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (photo_id, user_id)
);

-- Supports the "what's pending" comparison (D2), which joins available
-- photos against this table filtered by user_id, and cascading deletes
-- from either side.
create index photo_ratings_photo_id_idx on photo_ratings (photo_id);
create index photo_ratings_user_id_idx on photo_ratings (user_id);

create trigger set_photo_ratings_updated_at
before update on photo_ratings
for each row execute function set_updated_at();

-- Migration Plan: albums created before this change have no membership row
-- for their own owner, because that rule is born with this change. Without
-- this backfill, D9's "the album list is just membership" would hold only
-- for new albums and not for these -- the list would depend on when the
-- album was created, which is precisely what the design commits not to.
insert into album_members (album_id, user_id)
select id, owner_id from albums
on conflict do nothing;

-- migrate:down
drop table photo_ratings;
drop table album_members;
drop table share_tokens;
