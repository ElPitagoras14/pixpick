-- migrate:up
create table albums (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references users (id) on delete cascade,
  title text not null,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Supports listing a person's own albums (album-management spec) without a
-- sequential scan, the same reasoning as sessions_user_id_idx.
create index albums_owner_id_idx on albums (owner_id);

create trigger set_albums_updated_at
before update on albums
for each row execute function set_updated_at();

create table photos (
  id uuid primary key default gen_random_uuid(),
  album_id uuid not null references albums (id) on delete cascade,
  -- Assigned once, inside the same transaction as the insert (D12), and
  -- never changed afterward: there is no reorder operation.
  position integer not null,
  -- False from the moment a grant is issued, until confirmation verifies
  -- the object against what was declared (photo-upload spec). Every read
  -- other than the upload flow itself SHALL go through the view below,
  -- never this column directly (D1).
  available boolean not null default false,
  -- What the client declared when the grant was requested, checked
  -- against the real object at confirmation time -- never trusted on its
  -- own (photo-upload spec).
  declared_content_type text not null,
  declared_size integer not null,
  -- The object's real size, filled in only once confirmation verifies it.
  -- Null for every photo that isn't available yet.
  size integer,
  -- A presentation hint only (photo-upload spec): declared by the client,
  -- used to reserve layout space, and never involved in any authorization,
  -- validation, storage or delivery decision.
  width integer,
  height integer,
  -- The upload grant's own deadline. Drives two things: whether a pending
  -- photo still occupies a slot toward the album's maximum (D14), and what
  -- the reconciliation command (D8) is allowed to discard.
  upload_expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (album_id, position)
);

-- Supports both the count/cover lateral (D9) and reconciliation's scan for
-- expired pending rows (D8), neither of which should be a sequential scan.
create index photos_album_id_idx on photos (album_id);

create trigger set_photos_updated_at
before update on photos
for each row execute function set_updated_at();

-- The one place "available" is decided (D1): every read of photos other
-- than the upload flow's own writes goes through this view, so there is no
-- condition to remember or to forget in a later query.
create view available_photos as
select *
from photos
where available = true;

-- migrate:down
drop view available_photos;
drop table photos;
drop table albums;
