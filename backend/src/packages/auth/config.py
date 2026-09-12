from datetime import timedelta

# D5: fixed, not configurable, and not renewed on use.
SESSION_LIFETIME = timedelta(days=30)
SESSION_COOKIE_NAME = "session"

# Short-lived (D3): only needs to survive the round trip through the
# provider, never a whole session's worth of time.
STATE_COOKIE_LIFETIME = timedelta(minutes=15)
STATE_COOKIE_NAME = "auth_state"
RETURN_TO_COOKIE_NAME = "auth_return_to"

# Scopes the two cookies above: neither is needed by any request outside
# the auth flow itself, unlike the session cookie, which every request
# carries.
AUTH_COOKIE_PATH = "/api/auth"

DEFAULT_RETURN_TO = "/home"
