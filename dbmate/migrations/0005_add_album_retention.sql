-- migrate:up
-- Volatile default (`now()`) forces a rewrite that evaluates it once for
-- the whole statement, so every existing album gets the instant this
-- migration ran rather than its own creation date (album-retention design,
-- Migration Plan) -- inserts after this point get their own `now()` at
-- creation, exactly as a freshly created album should.
alter table albums add column renewed_at timestamptz not null default now();

-- migrate:down
alter table albums drop column renewed_at;
