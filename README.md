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
| `storage`        | Object storage (MinIO). The browser writes to it directly              | Yes -- `MINIO_PORT` (the browser writes to it directly) |
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

`compose.yaml` names its own four images (`migrate`, `backend`, `frontend`, `nginx`) as `ghcr.io/elpitagoras14/pixpick-*:latest` -- what a real deployment would pull, once something publishes them there, which nothing does yet. `compose.dev.yaml` is what builds each one from its own Dockerfile instead, tagging the result with that same name rather than pulling it; the two files together are what every command on this page uses, and picking up a code change in container mode means rebuilding (`docker compose -f compose.yaml -f compose.dev.yaml up --build backend`), not just editing and reloading.

### Native mode

The backend and the frontend can also run directly on the host instead of in containers, while every third-party service -- Postgres, the object storage, the image transformer, and nginx (needed here too, since the transformer publishes no port of its own) -- still runs via Compose:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d postgres migrate storage storage-init transformer nginx

cd backend
uv sync
PUBLIC_URL=http://localhost:3000 uv run python -m src.main   # http://localhost:8000, reloads on change since ENVIRONMENT=development

cd frontend
pnpm install
pnpm dev                          # http://localhost:3000, proxies /api and /images to the backend and nginx
```

Both modes read the same `.env` and the same variable names (see the comments in `.env.example`); only which process serves the backend and the frontend changes, plus the value of `MINIO_SERVER_ENDPOINT` (native mode reaches MinIO by its published host port; containers mode reaches it by its service name, like `DATABASE_URL` above). Open `http://localhost:3000` in this mode -- the frontend dev server keeps a single origin by proxying `/api` to the backend itself and `/images` to nginx (the transformer is never reachable directly, in either mode), the same way `nginx` does in the container mode above.

`PUBLIC_URL` is the one exception to "same `.env`, same values" above, and only in native mode: signing in builds its final redirect from `PUBLIC_URL` rather than from the request's own host (deliberately -- see `auth.router.callback`), so it has to be overridden to the frontend dev server's own address for that redirect to land somewhere that's actually serving the app. Left at `.env`'s own value (nginx's address, `http://localhost:8080`), the browser lands there right after signing in and gets a gateway error, since native mode's whole point is that nothing is listening for it there.

### Signing in

`IDENTITY_PROVIDER` selects which identity provider the backend authenticates people against: `local` or `google`.

`local` is a credential-less sign-in screen the backend itself serves, so the rest of the app -- and anyone developing against it -- never needs real OAuth credentials. Click "Continue" on the login page, type any email on the screen that follows, and you're signed in as that person. It only works when `ENVIRONMENT=development`: the code it accepts isn't backed by anything a stranger couldn't also send, so the backend refuses to start with `IDENTITY_PROVIDER=local` under any other `ENVIRONMENT`, naming the reason in the startup error instead of silently exposing it. Development stays on `local` even once `google` is configured elsewhere -- it's not something to switch to just to click through the real consent screen.

`google` signs people in with the Google account they already have -- the difference, for someone who only opened an album's share link, between rating it and closing the tab. Setting it up:

1. In the [Google Cloud console](https://console.cloud.google.com/apis/credentials), create an OAuth client ID of type "Web application".
2. Add an authorized redirect URI of `<PUBLIC_URL>/api/auth/google/callback` -- for example `http://localhost:8080/api/auth/google/callback` against this project's own default `PUBLIC_URL`. It has to match **exactly** what the backend builds from `PUBLIC_URL`; a mismatch comes back as an error from Google itself, not from this app, and the backend logs the address it's using at startup so the two can be compared instead of guessed at.
3. Configure the consent screen with the three minimal scopes: `openid`, `email`, `profile`. The console labels each scope's own sensitivity when you add it; confirming all three show as "non-sensitive" is what confirms the app doesn't need to go through Google's verification process (see below).
4. Copy the client ID and client secret the console issues into `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`, and set `IDENTITY_PROVIDER=google`.

Because the scopes above are the minimal, non-sensitive ones, the app can be used without submitting it to Google's verification review -- that review exists for apps that request sensitive or restricted scopes, which this one never does. If Google ever required it anyway, the fallback isn't to rush a review but to keep the app in testing mode with people added explicitly as test users: enough for sharing albums among people you know, not for an album shared publicly.

## Photos: storage and image variants

Uploads go straight from the browser to the object storage -- the backend only issues a signed grant for a single object, and never sees the file's bytes (`backend/src/storage/`). `STORAGE_PROVIDER` selects which storage provider is active: `local` (MinIO, running in this compose) or `r2` (Cloudflare R2, see "Cloud provider set" below).

Every image is delivered as one of three fixed, named variants -- never as the original, and never with a caller-chosen size:

| Variant     | Used for                          | Definition                                           |
| ----------- | ---------------------------------- | ----------------------------------------------------- |
| `thumbnail` | The gallery grid                   | 400x400, cropped to a square                          |
| `rating`    | The swipe/rating card               | Fits within 1080x1080, never cropped                  |
| `viewer`    | The full-screen viewer              | Fits within 2048x2048, never cropped                  |

All three are WebP, and none ever enlarges an original that's smaller than the variant. The full definition of each -- size, quality, and crop behavior -- lives in exactly one place: `backend/src/images/catalog.py`, translated to each provider's own vocabulary by its adapter (`backend/src/images/adapters/`) -- the catalog itself never changes with the provider. `IMAGE_PROVIDER` selects which transformer provider builds their addresses: `local` (imgproxy, running as the `transformer` service) or `imagekit` (see "Cloud provider set" below).

A variant's address encodes its own definition (its size, quality and format all appear, signed, in the URL itself). That's why changing anything in the catalog invalidates the cache **by itself**: the changed variant gets a new address, so the cache in front of it -- nginx locally, ImageKit's own CDN in cloud mode -- simply never serves the old definition again, and the previous address just ages out on its own. Nothing needs to be cleared and the transformer needs no restart.

In local mode, `nginx` (`nginx/nginx.conf`) is what actually caches produced variants, keyed by their full address, bounded to 2 GB and 30 days of inactivity; it also keeps serving an already-produced variant if the transformer goes down. Neither the storage nor the transformer are reachable directly from the browser (except the storage's uploads, which need their own origin, see `MINIO_ALLOWED_ORIGINS` in `.env.example`) -- every delivered image goes through `nginx`. In cloud mode, ImageKit's own CDN is what serves and caches a variant; `nginx`'s own `/images` route stays in place unused (D5 in `add-media-ports-and-local-adapters`) rather than becoming conditional.

To inspect what's actually in the local storage, run the `mc` CLI against it (same image and credentials `storage-init` uses; swap them in if you changed `.env`'s defaults):

```bash
docker run --rm --network pixpick_pixpick --entrypoint sh \
  quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z -c '
    mc alias set local http://storage:9000 pixpick pixpick_dev_password
    mc ls --recursive local/pixpick
  '
```

### Cloud provider set

`local` (MinIO, imgproxy) is for development. The cloud provider set -- Cloudflare R2 for storage, ImageKit for image transformation -- is for when other people are actually looking at the photos: R2 charges nothing for outbound traffic, and ImageKit is itself a CDN, so someone far from the server gets their photos from a point near them instead.

`STORAGE_PROVIDER` and `IMAGE_PROVIDER` are independent, so mixing them -- R2 with imgproxy, or MinIO with ImageKit -- is a valid combination, not just the two pairings above. **A self-hosted MinIO can't stay purely private on the VPS in either case**, though: the browser writes to the storage directly, from wherever the person using the app actually is, never from inside the VPS's own network (object-storage spec) -- true regardless of which transformer is active, imgproxy included. Pairing MinIO with ImageKit adds a second reason: unlike imgproxy, which shares the compose's private network with MinIO, ImageKit runs on a third party's own infrastructure and has to reach MinIO over the public internet to read originals. `MINIO_ALLOWED_ORIGINS` doesn't change this -- it's a browser-only check (which origins may write via CORS), never a network-level one, so it neither grants ImageKit access nor was ever what MinIO's public exposure was for.

**Setting up R2:**

1. Cloudflare dashboard -> Storage & databases -> R2 -> create a bucket.
2. In the bucket's Settings -> CORS policy, add a policy allowing the origins that need to upload directly (the same ones `MINIO_ALLOWED_ORIGINS` names), methods `PUT`, `GET`, `HEAD`.
3. R2 -> Manage API Tokens -> create a token scoped to this bucket with "Object Read & Write" permission. Copy the Access Key ID, Secret Access Key, and note the Account ID (it's part of the endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`).

**Setting up ImageKit:**

1. Create an account at imagekit.io and note its URL Endpoint (`https://ik.imagekit.io/<your_id>`) and Private Key.
2. Add a custom origin pointed at the R2 bucket above, using the same credentials from step 3 above -- ImageKit reads originals from it directly, the same way imgproxy reads from MinIO locally.
3. Enable "restrict unsigned URLs" for that origin: every variant address this project builds is already signed (`backend/src/images/adapters/imagekit.py`), and this is what makes ImageKit actually enforce it.

**Configuration:** MinIO and R2 keep entirely separate variables -- `MINIO_*` and `R2_*` (D9 in `add-cloud-media-adapters`) -- so filling in R2's group never touches MinIO's, and the reverse. Fill in `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` from the token, `R2_BUCKET` with the bucket's name, and `R2_ENDPOINT` with the R2 endpoint (a single address -- R2 is public from every side, D7 in `add-cloud-media-adapters`); do the same for `IMAGEKIT_URL_ENDPOINT`/`IMAGEKIT_PRIVATE_KEY`. Only then set `STORAGE_PROVIDER=r2` and `IMAGE_PROVIDER=imagekit` to actually make them the active pair -- at least one group has to be filled in to match whichever value these two name. Also switch `POSTGRES_DB` (and `DATABASE_URL`) to a different database name -- see "Provider sets have their own database" below -- and, when running in containers mode, clear `COMPOSE_PROFILES` so `storage`/`storage-init`/`transformer` don't start for nothing.

**Provider sets have their own database.** The execution mode (containers or native) only changes which host reaches Postgres; the provider set changes which database holds the data (D4 in `add-cloud-media-adapters`). Alternating between `local` and the cloud set during development, each with its own `POSTGRES_DB`, finds its own albums, photos and ratings intact every time -- neither one resets or hides the other's.

**Changing the active storage provider on an environment that already has data** is copy, check, switch, in that exact order -- never switch first:

1. Copy every object from the current provider to the destination, using each provider's own tools (this project's code deliberately never does this move).
2. Run the migration check against the destination -- it builds a port from that provider's own group of settings (`MINIO_*` or `R2_*`), regardless of which one `STORAGE_PROVIDER` currently names, so the environment keeps serving from the current provider the whole time:
   ```bash
   cd backend
   uv run python -m src.packages.photos.reconcile --against r2
   ```
   This lists every object the destination is still missing. Repeat the copy and this check until it reports none.
3. Only then change `STORAGE_PROVIDER` (and redeploy or restart). An object's name never depends on the provider it's stored in (object-storage spec), so once the copy is verified complete, every existing reference resolves against the new provider without touching a single row.

Rolling back is setting `STORAGE_PROVIDER` back to its previous value -- safe for as long as the previous provider's content still exists, so don't delete it until the new one has been in real use, not just checked.

## Albums and uploads

Create an album, then upload photos to it from the album's own page: pick one or more files, and each uploads on its own, with its own progress and its own retry if it fails. A photo only appears in the album -- in the grid, in its photo count, as its cover -- once its upload is actually confirmed; a photo whose upload never finishes never shows up anywhere, and never counts against anything.

Uploading is two steps, neither of which ever sends the file's bytes through the API: the client asks for a batch of upload grants, writes each file straight to the object storage with the grant it got, and then confirms the batch. Confirming is what verifies the object actually landed -- checking its real size and type against what was declared, never trusting the client's word for it -- and only then marks the photo available.

| Setting | What it governs |
| ------- | ---------------- |
| `ALBUM_MAX_PHOTOS` | The most photos a single album admits (default `50`). A product constraint on the swipe-to-rate interaction, not a storage quota. |

The albums list separates what's yours from what's been shared with you into two groups, each showing how many albums it holds. Which group is selected lives in the page's own address, so reloading it, or sharing a link to it, keeps showing the same one.

`ALBUM_MAX_PHOTOS` only conditions *adding* photos: lowering it never removes a photo from an album that already exceeds it, and that album stays exactly as readable and usable as any other -- the only thing that stops working is granting it more. Raising it back, or freeing space by deleting a few photos, is all it takes to add again.

An upload grant expires after a while. If the file behind it is never actually uploaded, the photo stays invisible forever and is harmless on its own, but its row and (if the upload partially landed) its object still take up space. Run the reconciliation command whenever it's convenient -- there's no schedule that runs it automatically, on purpose (nothing it cleans up is observable until then):

```bash
cd backend
uv run python -m src.packages.photos.reconcile
```

The same command also runs the migration check `--against` a named provider instead of this cleanup -- see "Cloud provider set" above.

## Sharing and rating

Every album has a "Share" control, visible only to its owner: opening it fetches the album's current link, generating the first one if it has none yet -- opening the dialog never itself changes what's shared. Anyone who opens that link, once signed in, becomes a member of the album: they can see it, see its photos, and rate them, but only the owner can rename it, delete it, add or remove photos, or administer its link.

Regenerating the link revokes the current one and issues a new one in the same step, so an album never briefly has two live links or none. Revoking leaves the album without a link until a new one is generated. Neither one ever removes an existing member: whoever already entered keeps their access and every rating they've made, exactly as before. Only someone who hasn't entered yet is turned away by a revoked link -- and a link that's unknown, revoked, or well-formed but foreign to any album all answer identically, so none of the three ever confirms that an album exists.

Rating is a swipe: drag the card right to approve, left to reject, or use the on-screen buttons or the arrow keys -- the gesture is a shortcut, never the only way to complete a sequence. The deck shows exactly the album's available photos a person hasn't rated yet, in the album's own order; there's no separate "finished" flag anywhere -- what's pending is always the live difference between the album's photos and that person's own ratings, so uploading more photos to an album someone already finished makes those new photos pending for them again, automatically. Rating the same photo twice is harmless: the second one simply replaces the first. The owner rates their own album the same way anyone else does -- creating an album already makes its owner a member of it, with nothing special to set up first.

How many photos are still pending shows up in the albums list, inside the album itself, and in the gallery's own "unrated" filter below -- always the same number in all three, for whoever's looking, since it's the same comparison between the album's photos and that person's own ratings, read three different ways.

## Gallery and stats

Opening an album shows its gallery: every available photo, with a small indicator in one corner showing whether the person looking rated it, and how -- not calling it approved or rejected is its own visible state, distinct from either rating. The gallery has four filters -- all, approved, rejected, and still unrated -- each showing its own count without a request of its own, and the selected filter lives in the page's own address, so reloading it, or sharing a filtered link, shows the same view; an unrecognized filter falls back to "all" instead of failing. The "unrated" filter, the swipe sequence, and the album's pending count are the same comparison read three ways, so they can never disagree, and the gallery offers a direct path back into the swipe sequence whenever something is still unrated.

Tapping a photo's indicator changes its rating on the spot, through the very same operation the swipe sequence uses -- editing from the gallery isn't a second way to rate, just another entrance to the one that already exists. A photo that stops matching the active filter doesn't jump out of the grid the instant that happens; it leaves the next time that filter is asked for, so correcting a few photos in a row never feels like the grid is moving under your finger.

The owner additionally sees, for every photo, how many people approved it and how many rejected it, as a compact line under each thumbnail, plus a one-line summary of how many people rated something and how many ratings exist in total, in the gallery's own header. Those counts are a separate resource from the gallery itself -- nobody but the owner can fetch them, and the gallery's own response never carries them either -- computed fresh on every request, never stored, so a new rating or a change of mind shows up the moment it's asked for again.

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
| Object storage client | [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (S3-compatible protocol; used by the storage adapters) |
| Environment config   | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| CLI                   | [Typer](https://typer.tiangolo.com/) (the reconciliation/migration-check command) |
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

The storage and image-delivery contract suites (`backend/tests/storage/`, `backend/tests/images/`) run against the real `storage`/`transformer`/`nginx` services above, not only against the in-memory doubles -- that's why those need to already be up too, the same expectation the suite already has of Postgres. The storage suite's real-provider run always targets whichever one `STORAGE_PROVIDER` currently names (D3 in `add-cloud-media-adapters`); switch it to `r2` (with `R2_*` filled in) and run it again to exercise that adapter instead.

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
| Gesture / animation   | [@use-gesture/react](https://use-gesture.netlify.app/) (swipe detection) + [motion](https://motion.dev/) (`motion/mini`, the reduced release-animation engine) |
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
