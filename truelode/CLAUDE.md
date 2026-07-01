# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Truelode — digital chain-of-custody + battery-passport platform for Zimbabwean lithium. It follows each truckload mine → transport → processor → buyer and proves honest handling by reconciling **weight + grade + GPS** at every stage (mass-balance), then assembles the lineage into a scannable, tamper-evident passport. The defensible core ("the moat") is the accounting, not the QR: to cheat, the weighbridges, the lab assay, and the GPS must all reconcile at once.

Three deployables: `backend/` (Flask API), `web/` (Next.js), `weighbridge-agent/` (serial-scale CLI). `infra/` has docker-compose (Postgres+PostGIS, backend, web).

## Commands

All Python commands assume Windows venv paths (`.venv/Scripts/python`).

```bash
# Backend (SQLite by default — no DB install needed)
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python seed.py        # demo orgs/sites/route/users
.venv/Scripts/python run.py         # serves http://localhost:5000 (Socket.IO)
.venv/Scripts/python -m pytest -q                       # all tests
.venv/Scripts/python -m pytest tests/test_ledger.py -q  # one file
.venv/Scripts/python -m pytest -k massbalance -q        # one test by name

# Web
cd web
npm install
cp .env.local.example .env.local
npm run dev                          # http://localhost:3000 (binds 0.0.0.0)
npm run build                        # production build (also validates RSC/SSR boundaries)
npm run lint
npx tsc --noEmit                     # typecheck only

# Full stack via Docker (Postgres+PostGIS)
cd infra && docker compose up --build

# Weighbridge agent (posts a weigh event; --demo fakes a reading)
python weighbridge-agent/agent.py --token <jwt> --batch <batch_id> --kind PLANT_IN --demo
```

Demo logins (after `seed.py`): `<role>@truelode.test` / `password`, where role ∈ mine, transporter, processor, buyer, regulator, lab, admin. Two-minute demo script in `docs/DEMO.md`.

## Backend architecture

App-factory (`app/__init__.py`) + shared extension singletons (`app/extensions.py`: `db`, `jwt`, `migrate`, `socketio`). Three layers, strictly separated:

- **`app/api/`** — one Blueprint per domain, registered in `app/api/__init__.py`. Handlers orchestrate; they do not hold business logic.
- **`app/services/`** — the logic. The three that constitute the moat:
  - `ledger.py` — append-only SHA-256 **hash chain** over every state-changing event (`append()` binds `prev_hash` + payload hash + seq + actor; `verify_chain()` recomputes the whole chain).
  - `massbalance.py` — weight/grade reconciliation in vs out (transport and processing).
  - `signing.py` — Ed25519 passport signatures (key auto-generated to PEM on first use).
  - Plus `geofence.py` (shapely corridor checks), `realtime.py`, `entitlements.py`, `passport*.py`.
- **`app/models/`** — SQLAlchemy models. Domain enums are **plain string constants** in `models/enums.py` (stored as text columns), not Python `Enum`.

### The core write pattern — follow it

Every state-changing endpoint does the same three things before commit: write the model row, **append a ledger entry**, and **emit a realtime event**. See `api/trips.py`, `api/weigh.py`, `api/loadtickets.py`:

```python
db.session.add(row); db.session.flush()
ledger.append("EVENT_TYPE", {...payload...}, actor_id=get_jwt().get("sub"))
emit_event("event.name", row.to_dict(), roles=[...], org_ids=[...])
db.session.commit()
```

Skipping the ledger append breaks the audit guarantee; skipping the emit breaks live dashboards.

### Realtime

`services/realtime.py` `emit_event(event, data, roles=, org_ids=)` fans out to `role:<ROLE>`, `org:<id>`, and an `all` room. Clients connect, then `emit("subscribe", {role, account_id})` to join rooms (`api/sockets.py`). `socketio` runs `async_mode="threading"`.

### Multi-tenancy & authorization

`Account` (INDIVIDUAL or ENTERPRISE) owns `User`s (each with a `role`). Authorization is decorator-based in `api/utils.py`: `role_required(*roles)` (ADMIN always allowed), `owner_required` (ENTERPRISE account owner), `feature_required(feature)` (billing-tier entitlement via `services/entitlements.py`). JWT carries `sub`, `role`, `account_id`.

### Passport snapshot (immutable + signed)

`services/passport.py` `build_snapshot()` recursively walks batch lineage to origin and assembles sections via `passport_assemble.py` (lineage, weigh_stages, reconciliations, assays) and `passport_context.py` (transport, custody, esg). `issue()` serializes the snapshot to canonical JSON (`sort_keys=True, separators=(",",":")`), Ed25519-signs it, and stores the **immutable** snapshot. `GET /api/verify/<token>` (public, no auth) recomputes the signature against the stored snapshot and verifies the full ledger chain. **Changing snapshot shape changes the signed bytes** — treat the canonical-JSON form as a contract.

## Frontend architecture

Next.js App Router. One route directory per role under `web/app/` (`mine/`, `transporter/`, …) plus the public `web/app/verify/[token]/`. Shared `web/lib/`:

- `api.ts` — `get/post/patch/del` wrappers; reads the JWT from `localStorage` (`tl_token`) and sets the Bearer header.
- `auth.tsx` — `AuthProvider` React context; persists `user` + token to `localStorage`.
- `socket.ts` — singleton Socket.IO client; `subscribe(role, accountId)`.
- `config.ts` — `API_BASE`/`SOCKET_URL` **auto-derive from the browser host** (so a phone at `http://<ip>:3000` hits `http://<ip>:5000` with no per-device config); fall back to `localhost` on the server. Override with `NEXT_PUBLIC_API_BASE` / `NEXT_PUBLIC_SOCKET_URL`.
- `passport.ts` — shared `fetchPassport(token)` used by both the server page and the client view.

The verify page is **server-rendered**: `app/verify/[token]/page.tsx` is a server component that fetches server-side and exports `generateMetadata` (OpenGraph), then hands `initialData` to the client `components/PassportView.tsx`, which renders `PassportHeader` + one small presentational component per snapshot section (`Lineage`, `Reconciliation`, `Custody`, `Transport`, `Assays`, `Esg`, `Issuer`, `Anomalies`, `ChecksPanel`, `PublicKey`). Keep these section components small and empty-safe (snapshot fields may be missing). Verify badge is three-state: green only when signature + chain valid **and** no open flags; amber when valid but flags open; red when signature/chain fails.

## Config & data

Backend config in `backend/config.py`, loaded from env (`.env` via python-dotenv). Defaults: `SQLALCHEMY_DATABASE_URI=sqlite:///truelode.db`, dev secrets, 12h JWT, mass-balance/geofence tolerances. `run.py` calls `db.create_all()` for dev convenience; Flask-Migrate/Alembic is wired for real migrations. Docker uses Postgres+PostGIS via `DATABASE_URL`.

Tests use an in-memory SQLite app built from `TestConfig` (`backend/tests/conftest.py`); the `app` fixture creates and drops all tables per test.
