# P0-T02 — AFFiNE installation (22 Nov 2026)

**Status:** PARTIAL. The server is installed and healthy. The first-run administrator setup must be done by the owner,
because the agent does not create accounts or enter passwords. The backup and restore drill runs after the workspace
exists.

## Source and runtime identity (kept separate)

| Item | Value |
|---|---|
| Requested repository (source reference) | `aisle9/affine`, a fork of `toeverything/AFFiNE`, branch `canary`, commit `36bc78bf2c1a4dbcecd0bd5b150d54396e0ceaf3`. It is 881 commits behind upstream and adds only 2 CI/config commits. It has no releases; package version 0.22.4 |
| Actual runtime | **Upstream** AFFiNE Community self-host **v0.27.4**, the latest stable at installation (published 18 Aug 2026). The fork's own Compose recipe also points to upstream `ghcr.io/toeverything/affine` images. **This is not a build of the aisle9 fork** |
| App image | `ghcr.io/toeverything/affine:0.27.4` @ `sha256:b649f5ce2384ffdf13c23bccf81d759e15973d59d0b0058af65d895a84373099` (the app and migration services use the same image) |
| Redis | `redis:7.4` @ `sha256:2e3eb11462c4e3759e6972678dd051d150ff54b1e60714b3c33b701260172a90` |
| Postgres | `pgvector/pgvector:pg16` @ `sha256:484e838076e04939d27d3e176e91c86eea96236126023be8d3059761122e579f` |
| Release assets used | `docker-compose.yml` (sha256 `4174fe1b…be5`), `config.json.example` (`e34ff687…cb`) and `config.schema.json` (`47857d79…082`), all from the v0.27.4 GitHub release |
| Desktop client | AFFiNE desktop 0.27.4, installed earlier via winget (`ToEverything.AFFiNE`; hash verified by winget). It is compatible with the 0.27.4 server |

## Deployment (outside the repository)

- **Location:** `C:\Users\User\ptp-tools\affine-tracker\`, Compose project `ptp-affine-tracker`.
  - Compose sha256: `50781e3b…a7f`.
  - `config/config.json` sha256: `8065eb92…7b9` (server name "Patent-to-Pilot Tracker"; external URL `http://127.0.0.1:3010`;
    copilot disabled, so no paid AI is used).
- **Changes from the upstream template:**
  - pinned tags, with digests recorded above;
  - app bound to `127.0.0.1:3010` only; Postgres and Redis ports are not published;
  - a locally generated Postgres password in a private `.env` (ACL restricted to the user; never printed or committed),
    replacing `POSTGRES_HOST_AUTH_METHOD=trust`;
  - Postgres data in the named Docker volume `ptp-affine-tracker_ptp_affine_pg`;
  - blobs in `data/storage/`;
  - no fixed container names.
- **Prerequisites observed:**
  - Docker Desktop: client 29.8.0, server 29.8.0, Compose v5.5.1;
  - WSL 2 with distros `docker-desktop` and `Ubuntu`;
  - 15.7 GB RAM, 12 logical CPUs.
- **No existing AFFiNE server data was present:** this is a fresh deployment, so nothing was migrated. The desktop app's local
  data was not touched.

## Health

- `docker compose ps`:
  - `affine` running on 127.0.0.1:3010;
  - `affine_migration` exited 0;
  - `postgres` and `redis` healthy.
- `GET /info` returns `{"compatibility":"0.27.4","message":"AFFiNE 0.27.4 Server","type":"selfhosted"}`. `GET /` returns
  302 to `/admin/setup`, the first-run page.

## Remaining (owner step, then agent)

1. **Owner:** open http://127.0.0.1:3010 (the Claude browser pane already shows it) and complete the administrator
   setup: name, email and password. The agent never enters passwords.
2. **Agent:**
   - create the workspace `Patent-to-Pilot — Research and Product`;
   - import the dashboard and the six phase pages;
   - build the task table;
   - read back the result;
   - run a backup (`pg_dump` custom format plus storage and config) and a restore drill into a separate empty target;
   - verify a restart.
