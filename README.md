# pixpick

Share photo albums and rate photos with a swipe. **Python backend (FastAPI + uv)**, **React frontend (TanStack + Vite)**, and an nginx edge that puts both behind a single origin, all orchestrated with Docker Compose.

> License: [MIT](./LICENSE).

## Structure

```
pixpick/
├── backend/     # FastAPI API, managed with uv
├── frontend/    # React SPA with TanStack Router/Query and Vite
└── edge/        # nginx: the only door to the host
```

## Services

| Service    | What it does                                                          | Reachable from the host?                          |
| ---------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| `edge`     | Routes `/api` to the backend and everything else to the frontend      | Yes -- `EDGE_PORT` (the app's single entry point)   |
| `backend`  | FastAPI API, mounted under `/api`                                      | No -- only through `edge`                           |
| `frontend` | Builds the SPA once; serves it and receives its config at container start | No -- only through `edge`                        |
| `postgres` | Database                                                               | Yes -- `POSTGRES_PORT` (so a DB client can inspect it) |

The interface and the API are always requested from the same origin: the browser never talks to `backend` or `frontend` directly, only to `edge`.

## Getting started

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Open `http://localhost:${EDGE_PORT}` (`8080` by default). That single command builds every image, starts Postgres, the backend, the frontend, and the edge, and leaves the app ready -- no other manual step.

To stop everything (keeping the database volume): `docker compose -f compose.yaml -f compose.dev.yaml down`. Add `-v` to also drop the Postgres data.

### Native mode

The backend and the frontend can also run directly on the host instead of in containers, while Postgres still runs via Compose:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d postgres

cd backend
uv sync
uv run fastapi dev src/main.py   # http://localhost:8000

cd frontend
pnpm install
pnpm dev                          # http://localhost:3000, proxies /api to the backend
```

Both modes read the same `.env` and the same variable names (see the comments in `.env.example`); only which process serves the backend and the frontend changes. Open `http://localhost:3000` in this mode -- the frontend dev server keeps a single origin by proxying `/api` to the backend itself, the same way `edge` does in the container mode above.

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
| Environment config   | [python-dotenv](https://pypi.org/project/python-dotenv/) |

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
