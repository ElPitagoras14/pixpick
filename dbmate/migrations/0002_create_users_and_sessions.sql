-- migrate:up
create table users (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  provider_user_id text not null,
  email text,
  name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider, provider_user_id)
);

create trigger set_users_updated_at
before update on users
for each row execute function set_updated_at();

create table sessions (
  id uuid primary key default gen_random_uuid(),
  token_hash text not null unique,
  user_id uuid not null references users (id) on delete cascade,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Supports deleting a user's expired sessions on login without a
-- sequential scan of the whole table.
create index sessions_user_id_idx on sessions (user_id);

create trigger set_sessions_updated_at
before update on sessions
for each row execute function set_updated_at();

-- migrate:down
drop table sessions;
drop table users;
