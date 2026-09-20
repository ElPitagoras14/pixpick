-- migrate:up
-- Three limits are computed from the sum of this column, and the
-- application's own validation already rejects a non-positive value. This
-- is the one that still holds if another path ever writes it.
alter table photos add constraint photos_declared_size_positive check (declared_size > 0);

-- migrate:down
alter table photos drop constraint photos_declared_size_positive;
