# pixpick

Share a photo album with other people. They rate each photo with a swipe. You see what they liked.

The backend is Python with FastAPI. The frontend is React with Vite. An nginx service puts both behind one address. Everything runs with Docker Compose.

License: [MIT](./LICENSE).

## What you need

- Docker and the `docker compose` command.
- [uv](https://docs.astral.sh/uv/), to run the backend outside Docker.
- [pnpm](https://pnpm.io/), to run the frontend outside Docker.

You only need the last two if you run the backend or the frontend on your own machine.

## Start it

```bash
cp .env.example .env
docker compose up --build
```

Then open `http://localhost:8080`. The port comes from `NGINX_PORT` in `.env`.

That one command starts everything: `postgres`, `storage`, `transformer`, `backend`, `frontend` and `nginx`. It also applies the database migrations and creates the bucket the photos go into. There is no other step.

You do not pass `-f` to any command. The `.env` file names the two compose files in `COMPOSE_FILE`.

Add `--build` after you change the code. Without it, Compose starts the image it built before.

### See what each service gets

```bash
docker compose config
```

This prints every service with its final values, as Compose reads them from the compose files and from your `.env`. Change a value in `.env` and run it again to see the new one.

### Stop it

```bash
docker compose down
```

Add `-v` to also delete the database and the stored photos.

### Run the backend and the frontend on your machine

You can run those two outside Docker. The other services keep running in Docker:

```bash
docker compose up -d postgres migrate storage transformer nginx

cd backend
uv sync
PUBLIC_URL=http://localhost:3000 uv run python -m src.main

cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000` in this mode. The backend answers on port 8000. Both reload when you save a file.

`PUBLIC_URL` is the one value you change here. The backend sends you back to it after you sign in. In `.env` it points at nginx, which is not serving the app in this mode.

## Sign in

`IDENTITY_PROVIDER` in `.env` chooses how people sign in. It takes `local` or `google`.

`local` is a sign-in form the backend serves itself. Click "Continue", type any email, and you are that person. It needs no account anywhere. It only works while `ENVIRONMENT=development`. The backend refuses to start otherwise.

Keep `local` for development. Use `google` when other people need to open your albums.

### Google

1. Open the [Google Cloud console](https://console.cloud.google.com/apis/credentials). Create an OAuth client ID of type "Web application".
2. Add `<PUBLIC_URL>/api/auth/google/callback` as an authorized redirect URI. With the default `PUBLIC_URL` that is `http://localhost:8080/api/auth/google/callback`. It has to match exactly. The backend prints the address it uses when it starts.
3. Set the consent screen to three scopes: `openid`, `email` and `profile`. The console marks all three as non-sensitive.
4. Copy the client ID and the client secret into `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Set `IDENTITY_PROVIDER=google`.

## Cloud providers

The photos can live in Cloudflare R2 instead of the `storage` service. The small versions of each photo can come from ImageKit instead of the `transformer` service. `STORAGE_PROVIDER` and `IMAGE_PROVIDER` choose each one. They are independent, so you can change only one.

### Set up R2

1. In the Cloudflare dashboard, go to Storage & databases, then R2, and create a bucket.
2. Open the bucket's Settings, then CORS policy. Allow the same origins you have in `MINIO_ALLOWED_ORIGINS`, with the methods `PUT`, `GET` and `HEAD`.
3. Go to R2, then Manage API Tokens. Create a token for this bucket with "Object Read & Write". Copy the Access Key ID, the Secret Access Key and the Account ID.

Fill in `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET`. Set `R2_ENDPOINT` to `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.

### Set up ImageKit

1. Create an account at imagekit.io. Note its URL Endpoint and its Private Key.
2. Add a custom origin that points at the R2 bucket above. Use the same token from step 3.
3. Turn on "restrict unsigned URLs" for that origin.

Fill in `IMAGEKIT_URL_ENDPOINT` and `IMAGEKIT_PRIVATE_KEY`.

### Turn them on

1. Set `STORAGE_PROVIDER=r2` and `IMAGE_PROVIDER=imagekit`.
2. Set `POSTGRES_DB` to another name, and change the database name in `DATABASE_URL` to the same one. Each name keeps its own albums and photos.
3. Empty `COMPOSE_PROFILES`, so the `storage` and `transformer` services do not start.

The bucket in R2 has to exist before you start. The backend stops with an error if it does not.

### Move the photos to another provider

Do these three steps in this order. Do not change the provider first.

1. Copy every object to the new provider with that provider's own tools.
2. Check what is still missing:
   ```bash
   cd backend
   uv run python -m src.packages.photos.reconcile --against r2
   ```
   It lists the objects the new provider does not have yet. Copy again and check again until the list is empty.
3. Change `STORAGE_PROVIDER` and restart.

To go back, set `STORAGE_PROVIDER` to the old value. Keep the old content until the new provider has been in real use.

## When something does not work

Read the logs of one service:

```bash
docker compose logs -f backend
```

See the values a service really got:

```bash
docker compose config
```

List what is in the local storage:

```bash
docker run --rm --network pixpick_pixpick --entrypoint sh \
  quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z -c '
    mc alias set local http://storage:9000 pixpick pixpick_dev_password
    mc ls --recursive local/pixpick
  '
```

Change the user and the password if you changed them in `.env`.

An upload that never finishes leaves something behind in `postgres` and, sometimes, a file in `storage`. The app never shows it. Clean it up when you want:

```bash
cd backend
uv run python -m src.packages.photos.reconcile
```

## Run the tests

```bash
docker compose up -d postgres storage transformer nginx
cd backend
uv sync
uv run pytest
```

Some tests talk to the real `storage`, `transformer` and `nginx` services. That is why they have to be up.

The tests use their own database, next to the one you develop with. Its name is `<POSTGRES_DB>_test`. The tests create it and migrate it on the first run. You clean up nothing between runs.

The storage tests run against the provider in `STORAGE_PROVIDER`. Set it to `r2`, fill in the `R2_*` values, and run them again to test that one.

Lint and format the backend:

```bash
cd backend
uv run ruff format .
uv run ruff check .
```

Lint and format the frontend:

```bash
cd frontend
pnpm format
pnpm lint
```

## Where each part lives

```
pixpick/
├── backend/     # the API, in Python
├── dbmate/      # the database migrations, in SQL
├── frontend/    # the app you see, in React
└── nginx/       # nginx, the only service you open on your machine
```

### The services

| Service | What it does | Open on your machine |
| --- | --- | --- |
| `nginx` | Sends `/api` to the backend, `/images` to the transformer, and the rest to the frontend | Yes, on `NGINX_PORT` |
| `backend` | The API, under `/api` | No |
| `frontend` | The app | No |
| `postgres` | The database | Yes, on `POSTGRES_PORT` |
| `storage` | Where the photos are kept | Yes, on `MINIO_PORT` |
| `transformer` | Makes the small versions of each photo | No |
| `migrate` | Applies the database migrations once, then exits | No |

The browser only talks to `nginx`. `storage` is the one exception: the browser sends each photo straight to it.

`storage` and `transformer` only start when `COMPOSE_PROFILES=local`.

### The backend (`backend/`)

| What | Which one |
| --- | --- |
| Language | Python 3.13 |
| Packages | [uv](https://docs.astral.sh/uv/) |
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | [SQLAlchemy](https://www.sqlalchemy.org/) with [psycopg](https://www.psycopg.org/) |
| Settings and shapes | [Pydantic](https://docs.pydantic.dev/) |
| Logs | [loguru](https://github.com/Delgan/loguru) |
| Passwords | [bcrypt](https://pypi.org/project/bcrypt/) |
| Storage | [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) |
| Commands | [Typer](https://typer.tiangolo.com/) |
| Lint and format | [Ruff](https://docs.astral.sh/ruff/) |

The three sizes every photo is served in are written in `backend/src/images/catalog.py`.

### The database migrations (`dbmate/`)

The schema is plain SQL, applied with [dbmate](https://github.com/amacneil/dbmate) `2.35.1`.

Create a migration. Rename the new file to the next number, such as `0002_...`:

```bash
docker run --rm -v "$(pwd)/dbmate:/db" ghcr.io/amacneil/dbmate:2.35.1 new create_some_table
```

Apply the pending migrations. `docker compose up` already does this, so you only need it when you started `postgres` alone:

```bash
docker run --rm --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL="postgres://pixpick:pixpick_dev_password@host.docker.internal:5432/pixpick?sslmode=disable" \
  -v "$(pwd)/dbmate:/db" \
  ghcr.io/amacneil/dbmate:2.35.1 migrate
```

Change the port in that command if you changed `POSTGRES_PORT`.

`dbmate/schema.sql` holds the current schema. The command above writes it again every time.

### The frontend (`frontend/`)

| What | Which one |
| --- | --- |
| Language | TypeScript |
| Packages | [pnpm](https://pnpm.io/) |
| Build | [Vite](https://vite.dev/) |
| UI | [React 19](https://react.dev/) |
| Pages | [TanStack Router](https://tanstack.com/router) |
| Data | [TanStack Query](https://tanstack.com/query) |
| Styles | [Tailwind CSS v4](https://tailwindcss.com/) |
| Components | [shadcn](https://ui.shadcn.com/) on [Radix UI](https://www.radix-ui.com/) |
| Icons | [lucide-react](https://lucide.dev/) |
| Swipe | [@use-gesture/react](https://use-gesture.netlify.app/) with [motion](https://motion.dev/) |
| Shapes | [Zod](https://zod.dev/) |
| HTTP | [axios](https://axios-http.com/) |
| Lint and format | [Biome](https://biomejs.dev/) |

| Command | What it does |
| --- | --- |
| `pnpm dev` | starts the development server |
| `pnpm build` | builds for production |
| `pnpm preview` | serves that build |
| `pnpm generate-routes` | writes the router files again |
| `pnpm format` | formats the code |
| `pnpm lint` | looks for problems |
| `pnpm check` | both of the two above |

## Upgrade the dependencies

Backend:

```bash
cd backend
uv lock --upgrade
uv sync

uv self update
```

Frontend:

```bash
cd frontend
pnpm update --latest
pnpm install

corepack use pnpm@latest
```

If you do not use corepack, upgrade pnpm with `npm install -g pnpm@latest`.
