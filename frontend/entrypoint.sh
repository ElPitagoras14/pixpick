#!/bin/sh
set -eu

# Checked before anything is substituted: envsubst turns a missing
# variable into an empty string and still succeeds. The list is explicit
# rather than derived from the template, so adding a placeholder without
# declaring it required shows up in review.
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
