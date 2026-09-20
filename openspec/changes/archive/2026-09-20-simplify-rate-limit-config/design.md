## Context

`nginx/nginx.conf.template` gets its rate-limit numbers substituted at container start by `nginx/entrypoint.sh`, which reads them from seven environment variables (`RATE_LIMIT_ENABLED` plus six numeric ceilings). `RATE_LIMIT_ENABLED=false` works by raising all six numbers to `1000000` before substitution, since nginx has no directive meaning "this zone doesn't limit anything" (see the existing comments in both files). `compose.yaml` and `compose.dev.yaml` hand all seven to the `nginx` service; `.env.example` documents them as required. See proposal.md - Why for why none of the seven need to vary by deployment in practice.

## Goals / Non-Goals

**Goals:**
- Remove the seven env vars end to end (nginx template, entrypoint, both compose files, `.env.example`) with no leftover references.
- Keep the actual rate-limit values unchanged (same 600/50/30/5/20/5 numbers), so behavior at runtime does not change for anyone not currently using `RATE_LIMIT_ENABLED=false`.

**Non-Goals:**
- Changing the rate-limit values themselves, or the zones/locations they apply to.
- Touching `STATEMENT_TIMEOUT_MS`/`LOCK_TIMEOUT_MS`/`IDLE_IN_TRANSACTION_TIMEOUT_MS`, the transformer limits, the album length caps, or `RECONCILE_INTERVAL_SECONDS` — those are handled as plain code cleanup in the parent task, outside this change, because no spec constrains them.

## Decisions

**Hardcode in `nginx.conf.template`, not in `entrypoint.sh`.** The six numbers are used directly in `limit_req_zone`/`limit_conn_zone`/`limit_req`/`limit_conn` directives; writing them as plain nginx config instead of `${VAR}` placeholders removes the need for `envsubst` to touch them at all, and removes the corresponding entries from `entrypoint.sh`'s `required_vars` list and its `envsubst` variable list. Only `${STORAGE_PUBLIC_HOSTNAME}` remains substituted.

**Drop the `RATE_LIMIT_ENABLED=false` escape hatch entirely, no replacement.** The proposal already covers why (dev/tests can edit the constant directly); nothing in `entrypoint.sh` needs to branch on it anymore.

**Keep the exact same numeric values.** 600 rpm / burst 50 (general), 30 rpm / burst 5 (grants), 20 connections/IP, 5s retry-after — these are `.env.example`'s current defaults, so nobody who hasn't overridden them sees a behavior change.

## Risks / Trade-offs

- [Anyone who has `RATE_LIMIT_ENABLED=false` set locally loses that escape hatch on upgrade] → `.env.example`'s own removal makes this visible immediately (their `.env` still has the line, but nothing reads it anymore); README no longer suggests it as a workaround, and points at editing the template's literal numbers instead.
- [Anyone who overrode the six numeric values in their own `.env`, for a deployment that genuinely needed a different ceiling] → **BREAKING**, called out in the proposal; changing the ceiling now means editing `nginx/nginx.conf.template` and rebuilding/redeploying the `nginx` image, not editing `.env`.

## Open Questions

Ninguna: el reemplazo es mecánico (mover seis números literales de `.env`/`compose`/`entrypoint.sh` a la plantilla, borrar el interruptor) y la spec ya deja explícito qué comportamiento se preserva y cuál se retira.
