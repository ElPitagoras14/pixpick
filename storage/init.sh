#!/bin/sh
# Runs once against the storage and exits (the storage-init service in
# compose.yaml). Creates the bucket if it's missing, so a clean clone
# needs no manual step (object-storage spec). The origins allowed to
# upload are declared on the storage service itself instead
# (MINIO_API_CORS_ALLOW_ORIGIN in compose.yaml) -- MinIO has no working
# per-bucket CORS API for this script to call.
set -eu

mc alias set target "$STORAGE_SERVER_ENDPOINT" "$STORAGE_ROOT_USER" "$STORAGE_ROOT_PASSWORD"
mc mb --ignore-existing "target/$STORAGE_BUCKET"
