# pixpick

Share photo albums and rate photos with a swipe. **Python backend (FastAPI + uv)**, **React frontend (TanStack + Vite)**, and an nginx service that puts both behind a single origin, all orchestrated with Docker Compose.

> License: [MIT](./LICENSE).

## Structure

```
pixpick/
├── backend/     # FastAPI API, managed with uv
├── frontend/    # React SPA with TanStack Router/Query and Vite
└── nginx/       # nginx: the only door to the host
```

## Services

| Service         | What it does                                                          | Reachable from the host?                          |
| ---------------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| `nginx`          | Routes `/api` to the backend, `/images` to the transformer (with its cache), and everything else to the frontend | Yes -- `NGINX_PORT` (the app's single entry point) |
| `backend`        | FastAPI API, mounted under `/api`                                      | No -- only through `nginx`                          |
| `frontend`       | Builds the SPA once; serves it and receives its config at container start | No -- only through `nginx`                       |
| `postgres`       | Database                                                               | Yes -- `POSTGRES_PORT` (so a DB client can inspect it) |
| `storage`        | Object storage (MinIO). The browser writes to it directly              | Yes -- `STORAGE_PORT` (the browser writes to it directly) |
| `storage-init`   | Runs once, creates the storage's bucket, then exits                    | No                                                   |
| `transformer`    | Image transformer (imgproxy). Reads originals from `storage` on its own | No -- only through `nginx`, never directly          |

The interface and the API are always requested from the same origin: the browser never talks to `backend`, `frontend` or `transformer` directly, only to `nginx`. The one exception is `storage`: uploads go straight from the browser to it, which is why it (and only it, among this project's own services) publishes a port of its own.

## Getting started

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Open `http://localhost:${NGINX_PORT}` (`8080` by default). That single command builds every image, starts Postgres, the object storage and image transformer, the backend, the frontend, and nginx, and leaves the app ready -- no other manual step.

To stop everything (keeping the database volume): `docker compose -f compose.yaml -f compose.dev.yaml down`. Add `-v` to also drop the Postgres data.

The `backend` service has no dev-only override: it builds from `backend/Dockerfile` the same way in every environment for now, so picking up a backend code change in container mode means rebuilding it (`docker compose -f compose.yaml -f compose.dev.yaml up --build backend`), not just editing and reloading.

### Native mode

The backend and the frontend can also run directly on the host instead of in containers, while every third-party service -- Postgres, the object storage, the image transformer, and nginx (needed here too, since the transformer publishes no port of its own) -- still runs via Compose:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d postgres migrate storage storage-init transformer nginx

cd backend
uv sync
uv run uvicorn src.main:app --reload --loop src.loop:loop_factory   # http://localhost:8000

cd frontend
pnpm install
pnpm dev                          # http://localhost:3000, proxies /api and /images to the backend and nginx
```

Both modes read the same `.env` and the same variable names (see the comments in `.env.example`); only which process serves the backend and the frontend changes, plus the values of `STORAGE_SERVER_ENDPOINT` (native mode reaches the storage by its published host port; containers mode reaches it by its service name, like `DATABASE_URL` above). Open `http://localhost:3000` in this mode -- the frontend dev server keeps a single origin by proxying `/api` to the backend itself and `/images` to nginx (the transformer is never reachable directly, in either mode), the same way `nginx` does in the container mode above.

### Signing in

`IDENTITY_PROVIDER` selects which identity provider the backend authenticates people against. The only value this project supports so far is `local`: a credential-less sign-in screen the backend itself serves, so the rest of the app -- and anyone developing against it -- never needs real OAuth credentials. Click "Continue" on the login page, type any email on the screen that follows, and you're signed in as that person.

The `local` provider only works when `ENVIRONMENT=development`: the code it accepts isn't backed by anything a stranger couldn't also send, so the backend refuses to start with `IDENTITY_PROVIDER=local` under any other `ENVIRONMENT`, naming the reason in the startup error instead of silently exposing it.

## Photos: storage and image variants

Uploads go straight from the browser to the object storage (`storage`, MinIO in local development) -- the backend only issues a signed grant for a single object, and never sees the file's bytes (`backend/src/storage/`). `STORAGE_PROVIDER` selects which storage provider is active; `local` is the only value so far.

Every image is delivered as one of three fixed, named variants -- never as the original, and never with a caller-chosen size:

| Variant     | Used for                          | Definition                                           |
| ----------- | ---------------------------------- | ----------------------------------------------------- |
| `thumbnail` | The gallery grid                   | 400x400, cropped to a square                          |
| `rating`    | The swipe/rating card               | Fits within 1080x1080, never cropped                  |
| `viewer`    | The full-screen viewer              | Fits within 2048x2048, never cropped                  |

All three are WebP, and none ever enlarges an original that's smaller than the variant. The full definition of each -- size, quality, and crop behavior -- lives in exactly one place: `backend/src/images/catalog.py`. `IMAGE_PROVIDER` selects which transformer provider builds their addresses; `local` (imgproxy, running as the `transformer` service) is the only value so far.

A variant's address encodes its own definition (its size, quality and format all appear, signed, in the URL itself). That's why changing anything in the catalog invalidates the cache **by itself**: the changed variant gets a new address, so nginx's cache -- which keys purely on the requested address -- simply never serves the old definition again, and the previous address just ages out on its own. Nothing needs to be cleared and the transformer needs no restart.

`nginx` (`nginx/nginx.conf`) is what actually caches produced variants, keyed by their full address, bounded to 2 GB and 30 days of inactivity; it also keeps serving an already-produced variant if the transformer goes down. Neither the storage nor the transformer are reachable directly from the browser (except the storage's uploads, which need their own origin, see `STORAGE_ALLOWED_ORIGINS` in `.env.example`) -- every delivered image goes through `nginx`.

To inspect what's actually in the local storage, run the `mc` CLI against it (same image and credentials `storage-init` uses; swap them in if you changed `.env`'s defaults):

```bash
docker run --rm --network pixpick_pixpick --entrypoint sh \
  quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z -c '
    mc alias set local http://storage:9000 pixpick pixpick_dev_password
    mc ls --recursive local/pixpick
  '
```

## Backend (`backend/`)

| Category           | Technology                                     |
| ------------------- | ----------------------------------------------- |
| Language / runtime   | Python >= 3.13                                 |
| Package manager      | [uv](https://docs.astral.sh/uv/)               |
| Web framework        | [FastAPI](https://fastapi.tiangolo.com/) (`standard` extra, includes Uvicorn) |
| ORM / DB driver      | [SQLAlchemy](https://www.sqlalchemy.org/) + [psycopg](https://www.psycopg.org/) (PostgreSQL) |
| Validation / config  | [Pydantic](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Logging              | [loguru](https://github.com/Delgan/loguru)     |
| Security             | [bcrypt](https://pypi.org/project/bcrypt/) (password hashing) |
| Object storage client | [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (S3-compatible protocol; used by the storage adapter) |
| Environment config   | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Lint / format         | [Ruff](https://docs.astral.sh/ruff/)           |

### Database migrations (`dbmate/`)

The schema evolves as plain SQL migrations applied with [dbmate](https://github.com/amacneil/dbmate), pinned to `2.35.1` -- the same version everywhere it's referenced (`dbmate/Dockerfile`, `backend/tests/conftest.py`, and here; see that Dockerfile's comment if you're upgrading it).

```bash
# create a new migration -- rename the generated file to the next
# zero-padded number (e.g. 0002_...) to match the existing ones
docker run --rm -v "$(pwd)/dbmate:/db" ghcr.io/amacneil/dbmate:2.35.1 new create_some_table

# apply pending migrations against the dev database and regenerate
# dbmate/schema.sql (compose already runs this via the `migrate` service on
# `docker compose up`; use this directly if you only started `postgres`)
docker run --rm --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL="postgres://pixpick:pixpick_dev_password@host.docker.internal:${POSTGRES_PORT:-5432}/pixpick?sslmode=disable" \
  -v "$(pwd)/dbmate:/db" \
  ghcr.io/amacneil/dbmate:2.35.1 migrate
```

`dbmate/schema.sql` is versioned so the schema can be read and diffed without running anything; the `migrate` command above regenerates it every time, whether or not it actually applied a new migration.

### Tests

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d postgres storage storage-init transformer nginx
cd backend
uv sync
uv run pytest
```

The storage and image-delivery contract suites (`backend/tests/storage/`, `backend/tests/images/`) run against the real `storage`/`transformer`/`nginx` services above, not only against the in-memory doubles -- that's why those need to already be up too, the same expectation the suite already has of Postgres.

Runs against the same Postgres the dev environment uses, on a separate `<POSTGRES_DB>_test` database (`pixpick_test` by default) that the suite creates and migrates itself, with the pinned dbmate version above, the first time it runs. No other setup, and no manual cleanup between runs.

### Lint & format

```bash
cd backend
uv run ruff format .   # formats the code
uv run ruff check .    # lints; add --fix to auto-fix what it can
```

### Upgrade dependencies to the latest version

```bash
cd backend
uv lock --upgrade    # recomputes uv.lock with the latest allowed versions
uv sync              # installs whatever ended up in the updated lockfile

# upgrade uv itself
uv self update
```

## Frontend (`frontend/`)

| Category            | Technology                                                       |
| -------------------- | ------------------------------------------------------------------ |
| Language / runtime    | TypeScript, Node.js                                              |
| Package manager       | [pnpm](https://pnpm.io/)                                         |
| Build tool            | [Vite](https://vite.dev/)                                        |
| UI library            | [React 19](https://react.dev/)                                   |
| Routing               | [TanStack Router](https://tanstack.com/router) (+ devtools, route generation via `tsr`) |
| Data fetching / cache | [TanStack Query](https://tanstack.com/query) (+ devtools)        |
| Styling               | [Tailwind CSS v4](https://tailwindcss.com/) + [tw-animate-css](https://www.npmjs.com/package/tw-animate-css) |
| UI components         | [shadcn](https://ui.shadcn.com/) on top of [Radix UI](https://www.radix-ui.com/) |
| Icons                 | [lucide-react](https://lucide.dev/)                               |
| UI utilities          | class-variance-authority, clsx, tailwind-merge                   |
| Data validation       | [Zod](https://zod.dev/)                                           |
| HTTP client           | [axios](https://axios-http.com/)                                  |
| Typography            | [@fontsource-variable/inter](https://fontsource.org/fonts/inter)  |
| Lint / format         | [Biome](https://biomejs.dev/)                                     |

### Available scripts

| Script                | Description                              |
| ---------------------- | ------------------------------------------ |
| `pnpm dev`              | starts the development server (Vite)      |
| `pnpm build`            | production build                          |
| `pnpm preview`          | serves the production build locally       |
| `pnpm generate-routes`  | regenerates TanStack Router routes (`tsr generate`) |
| `pnpm format`           | formats the code with Biome               |
| `pnpm lint`             | runs the linter (Biome)                   |
| `pnpm check`            | lint + format check with Biome            |

### Upgrade dependencies to the latest version

```bash
cd frontend
pnpm update --latest   # updates package.json and pnpm-lock.yaml to the latest versions
pnpm install            # makes sure node_modules stays in sync

# upgrade pnpm itself
corepack use pnpm@latest
# or, if you don't use corepack:
npm install -g pnpm@latest
```

> Note: `latest` in `@tanstack/react-devtools`, `@tanstack/react-router`, `@tanstack/react-router-devtools`, `@tanstack/devtools-vite`, and `@tanstack/router-plugin` always resolves to the most recently published version; `pnpm update --latest` still revalidates them along with everything else.
