# Truelode

Digital chain-of-custody + battery-passport platform for Zimbabwean lithium.
Follows each truckload mine → transport → processor → buyer and proves it was dug
and moved honestly by reconciling **weight + grade + GPS** at every stage
(mass-balance), then assembles the lineage into a scannable, tamper-evident passport.

> The moat is the accounting, not the QR. To cheat you must make the weighbridges,
> the lab assay, and the GPS all reconcile at once.

## Layout

| Path | What |
|---|---|
| `backend/` | Flask API + Socket.IO, SQLAlchemy models, mass-balance / geofence / ledger / passport services |
| `web/` | Next.js app — one live dashboard per role (mine, transporter, processor, buyer, regulator, lab, admin) + public `/verify/<token>` |
| `weighbridge-agent/` | reads a serial scale → POSTs weigh events (`--demo` mode included) |
| `infra/` | docker-compose (Postgres+PostGIS, backend, web) |

## Run it (local, zero infra)

```bash
# Backend  (SQLite by default — no DB to install)
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python seed.py        # demo orgs/sites/route/users
.venv/Scripts/python run.py         # http://localhost:5000

# Web
cd web
npm install
cp .env.local.example .env.local
npm run dev                          # http://localhost:3000
```

Demo logins: `<role>@truelode.test` / `password`
(roles: mine, transporter, processor, buyer, regulator, lab, admin).

### Reach it from other devices on the LAN

Backend already binds `0.0.0.0` and `web` serves on all interfaces (`next dev -H 0.0.0.0`).
With `NEXT_PUBLIC_API_BASE` / `NEXT_PUBLIC_SOCKET_URL` left unset, the web app auto-targets
whatever host you loaded it from — so just open `http://<host-LAN-IP>:3000` from a phone or
laptop on the same Wi-Fi (find the IP via `ipconfig` → IPv4).

On Windows, allow inbound TCP 3000 + 5000 once, in an **elevated** PowerShell:

```powershell
New-NetFirewallRule -DisplayName "Truelode web 3000"     -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3000
New-NetFirewallRule -DisplayName "Truelode backend 5000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000
```

## Tests

```bash
cd backend && .venv/Scripts/python -m pytest -q
```

Covers ledger hash-chain integrity + tamper detection, mass-balance math,
geofence corridor checks, and a full HTTP end-to-end flow
(load ticket → off-route flag → weight-mismatch → processing → signed passport → verify).

See `docs/DEMO.md` for the two-minute demo script.
