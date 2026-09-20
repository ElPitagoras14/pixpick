#!/bin/sh
set -eu

# Phase 1: validate every required variable is present before touching
# anything, same as the frontend's own entrypoint (D3 in
# harden-local-profile's design): envsubst alone can't be trusted for
# this, since a missing variable just becomes an empty string. The list
# is explicit here, not derived from the template, so adding a
# placeholder without declaring it required is visible in review.
required_vars="STORAGE_PUBLIC_URL"

for var in $required_vars; do
	eval "value=\${${var}:-}"
	if [ -z "$value" ]; then
		echo "entrypoint: missing required environment variable: $var" >&2
		exit 1
	fi
done

# The template's server_name needs a bare hostname, never the scheme or a
# port: nginx compares server_name against the Host header alone.
# Derived here, from the same STORAGE_PUBLIC_URL the backend receives as
# MINIO_BROWSER_ENDPOINT, so there is exactly one operator-facing value to
# keep the two in agreement -- not a second one that could drift from it.
STORAGE_PUBLIC_HOSTNAME=$(echo "$STORAGE_PUBLIC_URL" | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#[:/].*##')
if [ -z "$STORAGE_PUBLIC_HOSTNAME" ]; then
	echo "entrypoint: could not derive a hostname from STORAGE_PUBLIC_URL=$STORAGE_PUBLIC_URL" >&2
	exit 1
fi
export STORAGE_PUBLIC_HOSTNAME

# Phase 2: substitute and start nginx. Restricting envsubst's variable list
# keeps it from touching the file's own `$name`-shaped nginx variables
# (`$remote_addr`, `$http_x_forwarded_for`, and the rest). The rate and
# connection limits are fixed in the template itself (simplify-rate-
# limit-config), so this is the only placeholder left to substitute.
envsubst '${STORAGE_PUBLIC_HOSTNAME}' \
	< /etc/pixpick/nginx.conf.template \
	> /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
