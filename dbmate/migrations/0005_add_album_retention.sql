-- migrate:up
-- A volatile default (`now()`) forces a rewrite that evaluates it once for
-- the whole statement, so every album that already existed gets the
-- instant this migration ran rather than its own creation date. Inserts
-- after this point get their own `now()`, as a new album should.
alter table albums add column renewed_at timestamptz not null default now();

-- migrate:down
alter table albums drop column renewed_at;
