#!/bin/sh
set -eu

# Phase 1: validate every required variable is present before touching
# anything, same as the frontend's own entrypoint (D3 in
# harden-local-profile's design): envsubst alone can't be trusted for
# this, since a missing variable just becomes an empty string. The list
# is explicit here, not derived from the template, so adding a
# placeholder without declaring it required is visible in review.
required_vars="STORAGE_PUBLIC_URL API_RATE_LIMIT_PER_MINUTE API_RATE_LIMIT_BURST
GRANTS_RATE_LIMIT_PER_MINUTE GRANTS_RATE_LIMIT_BURST API_MAX_CONNECTIONS_PER_IP
RATE_LIMIT_RETRY_AFTER_SECONDS RATE_LIMIT_ENABLED"

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

# The rate and connection limits can be turned off by configuration
# (request-throttling spec: development and the test suite need to
# exercise the system at a pace a limit sized for the internet would cut
# off). nginx has no directive that means "this zone doesn't limit
# anything", so this raises the substituted values themselves to a
# ceiling nothing a real client does ever reaches, instead of the zones
# or the `limit_req`/`limit_conn` directives being conditionally written
# into the config at all.
if [ "$RATE_LIMIT_ENABLED" = "false" ]; then
	API_RATE_LIMIT_PER_MINUTE=1000000
	API_RATE_LIMIT_BURST=1000000
	GRANTS_RATE_LIMIT_PER_MINUTE=1000000
	GRANTS_RATE_LIMIT_BURST=1000000
	API_MAX_CONNECTIONS_PER_IP=1000000
	export API_RATE_LIMIT_PER_MINUTE API_RATE_LIMIT_BURST GRANTS_RATE_LIMIT_PER_MINUTE
	export GRANTS_RATE_LIMIT_BURST API_MAX_CONNECTIONS_PER_IP
fi

# Phase 2: substitute and start nginx. Restricting envsubst's variable list
# keeps it from touching the file's own `$name`-shaped nginx variables
# (`$remote_addr`, `$http_x_forwarded_for`, and the rest).
envsubst '${STORAGE_PUBLIC_HOSTNAME} ${API_RATE_LIMIT_PER_MINUTE} ${API_RATE_LIMIT_BURST} ${GRANTS_RATE_LIMIT_PER_MINUTE} ${GRANTS_RATE_LIMIT_BURST} ${API_MAX_CONNECTIONS_PER_IP} ${RATE_LIMIT_RETRY_AFTER_SECONDS}' \
	< /etc/pixpick/nginx.conf.template \
	> /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
