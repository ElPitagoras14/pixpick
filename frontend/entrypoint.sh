#!/bin/sh
set -eu

# Phase 1: validate every required variable is present before touching
# anything. envsubst alone can't be trusted for this: a missing variable
# becomes an empty string and the substitution still succeeds (D5). The
# list is explicit here, not derived from the template, so adding a
# placeholder without declaring it required is visible in review.
required_vars="API_BASE_URL ENVIRONMENT"

for var in $required_vars; do
	eval "value=\${${var}:-}"
	if [ -z "$value" ]; then
		echo "entrypoint: missing required environment variable: $var" >&2
		exit 1
	fi
done

# Phase 2: substitute and start nginx. Restricting envsubst's variable list
# to $required_vars keeps it from touching unrelated `$name`-shaped content
# nginx might emit elsewhere.
envsubst "$(printf '${%s} ' $required_vars)" \
	< /etc/pixpick/config.template.js \
	> /usr/share/nginx/html/config.js

exec nginx -g "daemon off;"
