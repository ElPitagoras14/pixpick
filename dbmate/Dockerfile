# Bakes this project's migrations and schema into the dbmate image, so
# whatever applies them (the migrate service below, backend/tests/conftest.py
# for the test database, or a deployment with prebuilt artifacts) does not
# need the repository checked out on the machine that runs it.
#
# The version is pinned and must stay identical everywhere it is referenced
# (database-migrations spec); after changing it here, update it in every
# other place it appears:
#   - backend/tests/conftest.py (DBMATE_IMAGE, migrates the test database)
#   - README.md (documents this version for the local dbmate CLI)
FROM ghcr.io/amacneil/dbmate:2.35.1

COPY migrations /db/migrations
COPY schema.sql /db/schema.sql
