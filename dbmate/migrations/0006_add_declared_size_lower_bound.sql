-- migrate:up
-- The database is the last defense of three limits that all depend on this
-- sum (photo-upload spec, D5 in harden-local-profile): the application's
-- own validation already rejects a non-positive value, but this is the one
-- that still holds if another path ever writes this column.
alter table photos add constraint photos_declared_size_positive check (declared_size > 0);

-- migrate:down
alter table photos drop constraint photos_declared_size_positive;
