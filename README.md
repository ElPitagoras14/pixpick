# Pixpick

Share a photo album with other people. They rate each photo with a swipe. You see what they liked.

The backend is Python with FastAPI. The frontend is React with Vite. An nginx service puts both behind one address. Everything runs with Docker Compose.

This page is written first for whoever runs Pixpick and keeps it going. Whoever works on the code will find their part in the last section, [Work on the code](#work-on-the-code).

License: [MIT](./LICENSE).

## What you need

- Docker and the `docker compose` command.

## Start it

Take `compose.yaml` and `.env.example` from this repository, put them in one folder, and run:

```bash
cp .env.example .env
docker compose up -d
```

Open `.env` before you do. `.env.example` marks what needs a value from you and explains every variable. [Get the values you need](#get-the-values-you-need) has the steps outside the repository that some of those values take.

That one command pulls the four Pixpick images and starts everything: `postgres`, `pixpick-migrate`, `storage`, `transformer`, `pixpick-backend`, `pixpick-frontend`, `pixpick-nginx` and `reconciler`. It also applies the database migrations and creates the bucket the photos go into. There is no other step.

`compose.yaml` opens no port. `pixpick-nginx` is the only service anyone has to reach, and what reaches it is up to you: see [Put it on a server](#put-it-on-a-server). To try the project on your own machine with a port open, see [Run it from source](#run-it-from-source).

## Get the values you need

Some values in `.env` cannot be made up: you get them by setting something up outside this repository. The steps are here. `.env.example` names each variable and says what it controls.

### Google

Needed for `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

1. Open the [Google Cloud console](https://console.cloud.google.com/apis/credentials). Create an OAuth client ID of type "Web application".
2. Add `<PUBLIC_URL>/api/auth/google/callback` as an authorized redirect URI. With the default `PUBLIC_URL` that is `http://localhost:8080/api/auth/google/callback`. It has to match exactly. The backend prints the address it uses when it starts.
3. Set the consent screen to three scopes: `openid`, `email` and `profile`. The console marks all three as non-sensitive.
4. Copy the client ID and the client secret into `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Set `IDENTITY_PROVIDER=google`.

### R2

Needed for `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` and `R2_ENDPOINT`.

1. In the Cloudflare dashboard, go to Storage & databases, then R2, and create a bucket.
2. Open the bucket's Settings, then CORS policy. Allow the same origins you have in `MINIO_ALLOWED_ORIGINS`, with the methods `PUT`, `GET` and `HEAD`.
3. Go to R2, then Manage API Tokens. Create a token for this bucket with "Object Read & Write". Copy the Access Key ID, the Secret Access Key and the Account ID.

Fill in `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET`. Set `R2_ENDPOINT` to `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. Then set `STORAGE_PROVIDER=r2`.

### ImageKit

Needed for `IMAGEKIT_URL_ENDPOINT` and `IMAGEKIT_PRIVATE_KEY`.

1. Create an account at imagekit.io. Note its URL Endpoint and its Private Key.
2. Add a custom origin that points at the R2 bucket above. Use the same token from step 3 of [R2](#r2).
3. Turn on "restrict unsigned URLs" for that origin.

Fill in `IMAGEKIT_URL_ENDPOINT` and `IMAGEKIT_PRIVATE_KEY`. Then set `IMAGE_PROVIDER=imagekit`.

### The storage hostname

Needed for `STORAGE_PUBLIC_URL`.

The browser writes photos to `storage` without going through the backend, but that write still goes through `pixpick-nginx`, which caps how much one upload can write before it reaches the storage. `pixpick-nginx` tells an upload from a request for the app by hostname: it matches the `Host` header against `STORAGE_PUBLIC_URL`, and everything else goes to the backend or the frontend.

So `STORAGE_PUBLIC_URL` needs a hostname, not a bare IP address -- with both under the same address there is nothing for nginx to match on. Three ways to get one:

- **A real domain.** Behind a platform proxy (Dokploy or otherwise) that already terminates TLS for `PUBLIC_URL`'s domain, give it a second domain for storage -- `storage.yourdomain.com` is the usual pattern -- pointed at the same `pixpick-nginx` service. Set `STORAGE_PUBLIC_URL` to that, with `https://`.
- **`storage.localhost`, for local development.** The default in `.env.example`. Every major browser resolves anything ending in `.localhost` to your own machine, with no `/etc/hosts` entry and no DNS server.
- **An sslip.io or nip.io hostname, for a private or VPN address with no domain.** These resolve a hostname that encodes an IP address to that address, so only the lookup leaves your network. For a machine at `192.168.1.50`, set `STORAGE_PUBLIC_URL=http://storage.192-168-1-50.sslip.io:8080` -- dots in the IP become dashes, and the port is whatever `NGINX_PORT` you use.

Whichever you pick, it is the only value that changes. `pixpick-nginx`'s configuration and the rest of `.env` stay as they are.

## Put it on a server

`compose.yaml` shows how the services fit together. It is not the only way to run them, and it makes no assumption about where. What the stack expects of the place it runs in:

- **One entry point.** `pixpick-nginx` is the only service the outside has to reach. Everything the browser asks for goes through it, photo uploads included.
- **Two public hostnames** that lead to that entry point: one for the site, in `PUBLIC_URL`, and one for photo uploads, in `STORAGE_PUBLIC_URL`. [The storage hostname](#the-storage-hostname) says how to get the second.
- **TLS ended outside the stack.** `pixpick-nginx` speaks plain HTTP, so whatever sits in front of it presents the certificate, and both URLs start with `https://`.
- **Its network named, if something sits in front.** `TRUSTED_PROXY_NETWORK` tells `pixpick-nginx` where that front comes from, so it can tell visitors apart. `.env.example` explains it.

### The rate limit and your CDN

Put a CDN in front of the instance and you want a matching rule there too, at whichever of the two limits under [When a request is rejected](#when-a-request-is-rejected) is stricter for the path: `pixpick-nginx`'s counters live in memory and reset on every restart, so the CDN's rule is what holds across one.

## Keep it running

### Back it up

Two volumes hold what someone would miss:

| Volume | What is lost without it |
| --- | --- |
| `postgres-data` | The database: every album, rating and account. |
| `storage-data` | The photos, when `STORAGE_PROVIDER=local`. With `r2` they live in the bucket and this volume is empty. |

Back both up with whatever you use for Docker volumes. The third volume, `nginx-cache`, holds the small versions `pixpick-nginx` keeps of each photo. They are made again from the originals on demand, so it needs no backup.

Stopping the project keeps all three:

```bash
docker compose down
```

Add `-v` to also delete them. That deletes the database and the stored photos.

### Move to a newer version

The four Pixpick images are pulled again on every `up`, so this needs only the compose file and your `.env`:

```bash
docker compose up -d
```

`pixpick-migrate` applies the new database migrations before the backend starts. Back up first. If the release changed `compose.yaml` or `.env.example`, take the new copies and compare `.env` against the new `.env.example` before you run it.

### Read the logs

Read the logs of one service:

```bash
docker compose logs -f pixpick-backend
```

### See the values a service got

```bash
docker compose config
```

This prints every service with its final values, as Compose reads them from the file and from your `.env`. Change a value in `.env` and run it again to see the new one.

### When a request is rejected

A request rejected with `"code": "rate_limited"` or `"insufficient_capacity"` means the rate limit or the database's own connection pool got in the way, not that anything you sent was wrong -- the response says how long to wait.

`pixpick-nginx` accepts 600 requests a minute from the same address, and 30 for asking to upload a photo. Both are fixed in the `pixpick-nginx` image, not something you toggle from `.env`.

### List what is in the local storage

```bash
docker run --rm --network pixpick_pixpick --entrypoint sh \
  quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z -c '
    mc alias set local http://storage:9000 pixpick pixpick_dev_password
    mc ls --recursive local/pixpick
  '
```

Change the user and the password if you changed them in `.env`.

### Clean up by hand

An upload that never finishes, or an album whose retention has run out, leaves something behind in `postgres` and, sometimes, a file in `storage`. The app never shows either one, and the `reconciler` service discards both on its own, every five minutes. Run it by hand when you do not want to wait out the interval, such as right after testing an expiry:

```bash
docker compose exec reconciler python -m src.maintenance.reconcile
```

It discards abandoned uploads and expired albums, with their photos and objects. `storage`, `postgres` and the image cache share one disk here, so leaving it to run is what keeps that disk from filling up.

## Move the photos elsewhere

Do these three steps in this order. Do not change the provider first.

1. Copy every object to the new provider with that provider's own tools.
2. Check what is still missing:
   ```bash
   docker compose exec reconciler python -m src.maintenance.reconcile --against r2
   ```
   It lists the objects the new provider does not have yet. Copy again and check again until the list is empty.
3. Change `STORAGE_PROVIDER` and restart.

To go back, set `STORAGE_PROVIDER` to the old value. Keep the old content until the new provider has been in real use.

## The services

| Service | What it does | Port on your machine |
| --- | --- | --- |
| `pixpick-nginx` | Sends `/api` to the backend, `/images` to the transformer, its own storage hostname to `storage`, and everything else to the frontend | `NGINX_PORT` |
| `pixpick-backend` | The API, under `/api` | None |
| `pixpick-frontend` | The app | None |
| `postgres` | The database | `POSTGRES_PORT` |
| `storage` | Where the photos are kept | `MINIO_PORT` (running from source only) |
| `transformer` | Makes the small versions of each photo | None |
| `pixpick-migrate` | Applies the database migrations once, then exits | None |
| `reconciler` | Discards abandoned uploads and expired albums on a schedule | None |

Only `compose.dev.yaml` opens ports. `compose.yaml` opens none.

The browser only talks to `pixpick-nginx`, including when it uploads a photo (see [The storage hostname](#the-storage-hostname)). `MINIO_PORT` publishes `storage`'s own port for running from source; the browser never uses it in containers mode.

Both files declare all eight. `storage` and `transformer` start even when `STORAGE_PROVIDER` and `IMAGE_PROVIDER` name a cloud provider. Those two variables decide who the app talks to, not which containers run.

## Work on the code

Everything from here on assumes a clone of this repository, and for some of it the development tools.

- [uv](https://docs.astral.sh/uv/), to run the backend outside Docker.
- [pnpm](https://pnpm.io/), to run the frontend outside Docker.

You only need those two if you run the backend or the frontend on your own machine.

### Run it from source

```bash
cp .env.example .env
docker compose -f compose.dev.yaml up --build
```

Then open `http://localhost:8080`. The port comes from `NGINX_PORT` in `.env`.

That one command starts all eight services in [The services](#the-services) and builds the four Pixpick images from the code in this repository. It also applies the database migrations and creates the bucket the photos go into. There is no other step.

Add `--build` after you change the code. Without it, Compose starts the image it built before.

`docker compose -f compose.dev.yaml config` is the same check as [See the values a service got](#see-the-values-a-service-got), against this file.

If you need to hammer the API without the rate limit getting in the way, edit the numbers directly in `nginx/nginx.conf.template` and rebuild `pixpick-nginx`.

#### The two compose files

There are two ways to start the same eight services. Each one is written in full, in its own file:

| File | What it does | How you start it |
| --- | --- | --- |
| `compose.dev.yaml` | builds the four images from the code in this repository, and opens ports on your machine | `docker compose -f compose.dev.yaml up` |
| `compose.yaml` | pulls those four images by tag, and opens no port | `docker compose up` |

Use `compose.dev.yaml` to work on the project. Every command in this section that builds or opens a port names it.

The two files are never mixed. Each one lists all eight services with everything they need, so you can read either one on its own. They say the same thing except for where each image comes from and which ports are open.

#### Stop it

```bash
docker compose -f compose.dev.yaml down
```

#### Run the backend and the frontend on your machine

You can run those two outside Docker. The other services keep running in Docker:

```bash
docker compose -f compose.dev.yaml up -d postgres pixpick-migrate storage transformer pixpick-nginx

cd backend
uv sync
PUBLIC_URL=http://localhost:3000 uv run python -m src.main

cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000` in this mode. The backend answers on port 8000. Both reload when you save a file. `PUBLIC_URL` is the one value you set differently here; `.env.example` explains it.

This one includes `pixpick-migrate` because the backend you run yourself needs the schema in place before it starts, and nothing else applies it. The command under [Run the tests](#run-the-tests) leaves it out: the tests create their own database and migrate it themselves.

The maintenance command from [Clean up by hand](#clean-up-by-hand) runs from `backend/` in this mode:

```bash
cd backend
uv run python -m src.maintenance.reconcile
```

### Run the tests

```bash
docker compose -f compose.dev.yaml up -d postgres storage transformer pixpick-nginx
cd backend
uv sync
uv run pytest
```

Some tests talk to the real `storage`, `transformer` and `pixpick-nginx` services. That is why they have to be up.

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

### Where each part lives

```
pixpick/
├── backend/     # the API, in Python
├── dbmate/      # the database migrations, in SQL
├── frontend/    # the app you see, in React
└── nginx/       # nginx, the only service you open on your machine
```

#### The backend (`backend/`)

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

#### The database migrations (`dbmate/`)

The schema is plain SQL, applied with [dbmate](https://github.com/amacneil/dbmate) `2.35.1`.

Create a migration. Rename the new file to the next number, such as `0002_...`:

```bash
docker run --rm -v "$(pwd)/dbmate:/db" ghcr.io/amacneil/dbmate:2.35.1 new create_some_table
```

Apply the pending migrations. Starting the project already does this, so you only need it when you started `postgres` alone:

```bash
docker run --rm --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL="postgres://pixpick:pixpick_dev_password@host.docker.internal:5432/pixpick?sslmode=disable" \
  -v "$(pwd)/dbmate:/db" \
  ghcr.io/amacneil/dbmate:2.35.1 migrate
```

Change the port in that command if you changed `POSTGRES_PORT`.

`dbmate/schema.sql` holds the current schema. The command above writes it again every time.

#### The frontend (`frontend/`)

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

### Upgrade the dependencies

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
