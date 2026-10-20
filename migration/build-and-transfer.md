# Off-host image build — Mission Control migration (Phase 3)

Images are built on the **operator workstation** (Docker 29.8.2, 8.1 GB RAM), never on a destination VM.
The FE/BE VMs have 956 MB RAM; `npm ci` + `vite build` needs ~1–1.5 GB and would be OOM-killed.

## Build source

The authoritative build source is the **server repository working tree**, not the local Windows checkout
(which is a divergent line with unrelated WIP). It is materialised locally as a clean clone:

```powershell
git clone --no-hardlinks --branch release/v3.0.0-rc1 --single-branch `
    "ssh://billboe3@34.35.177.209/opt/MissionControl" mc-build
```

## Build

```powershell
cd mc-build
$tag = "601a878-20261020"     # <source-revision-short-sha>-<build-date>
docker build --no-cache -t missioncontrol-backend:$tag  ./backend
docker build --no-cache -t missioncontrol-frontend:$tag ./frontend
```

`--no-cache` is deliberate: it prevents a stale layer from masking a `requirements.txt` or
`package-lock.json` change, which matters because the live deployment runs from a bind mount and its
dependency set is not verifiable from the image alone.

## Transfer (prepared, NOT executed in Phase 3 as executed)

```bash
docker save missioncontrol-backend:$tag  | gzip -1 > backend-$tag.tar.gz
docker save missioncontrol-frontend:$tag | gzip -1 > frontend-$tag.tar.gz
scp -i <key> *-$tag.tar.gz ubuntu@84.12.82.239:/tmp/      # backend  -> BE
scp -i <key> *-$tag.tar.gz ubuntu@84.12.77.251:/tmp/      # frontend -> FE
ssh ... "gunzip -c /tmp/backend-$tag.tar.gz | docker load"
```

`gzip -1` is used because the tarball is mostly already-compressed layer data; higher levels cost CPU and
RAM on the workstation for little gain.

## Digest ledger

Fill in after each build. The destination must be deployed from **this** recorded revision and digest.

| Image | Tag | Image ID (manifest) | Size |
|---|---|---|---|
| `missioncontrol-backend` | `601a878-20261020` | `sha256:81f8448974fcc5030310e527d67f791369ce52bbd5d8a7218a864227990d147d` | 603 MB |
| `missioncontrol-frontend` | `601a878-20261020` | `sha256:1ec76e71b65ea98fbcfc2454bd12d26c82fa7c6ae99ee2606eff2369c1c9c78e` | 75.6 MB |

## Verification after load on a destination

```bash
docker images --digests | grep missioncontrol
docker run --rm missioncontrol-backend:$tag python -c "import app.main"   # import smoke test
docker run --rm missioncontrol-frontend:$tag sh -c 'ls /usr/share/nginx/html | head'
```
