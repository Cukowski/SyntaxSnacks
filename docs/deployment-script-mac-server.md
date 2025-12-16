# Deployment

## Mac Server Runner Script

This script automates the deployment process on a Mac server. It handles:
1. Activating the virtual environment.
2. Starting Gunicorn.
3. Checking for Git updates daily and restarting if changes are found.
4. Running a Cloudflare tunnel.

### Setup

1. Save the following script as `runner.sh`.
2. Make it executable: `chmod +x runner.sh`.
3. Update the `APP_DIR`, `VENV_ACTIVATE`, and tunnel name to match your environment.

```bash
#!/usr/bin/env bash

set -eu

# Configuration
APP_DIR="/Users/.../path/to/snacks"
VENV_ACTIVATE="/path/to/venv/bin/activate"
BRANCH="main"
REMOTE="origin"

cd "$APP_DIR" || exit 1

# Activate virtual environment
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

start_gunicorn() {
  gunicorn -w 2 -b 127.0.0.1:5000 app:app > gunicorn.log 2>&1 &
  GUNICORN_PID=$!
  log "Gunicorn started (PID $GUNICORN_PID)"
}

stop_gunicorn() {
  if [ -n "${GUNICORN_PID:-}" ] && kill -0 "$GUNICORN_PID" 2>/dev/null; then
    log "Stopping Gunicorn..."
    kill "$GUNICORN_PID" 2>/dev/null || true
    wait "$GUNICORN_PID" 2>/dev/null || true
    log "Gunicorn stopped."
  fi
}

restart_gunicorn() {
  stop_gunicorn
  start_gunicorn
}

update_repo_if_needed() {
  if [ ! -d ".git" ]; then
    log "Not a git repo, skipping update."
    return
  fi

  if ! git fetch "$REMOTE" "$BRANCH" --quiet; then
    log "git fetch failed, keeping current version."
    return
  fi

  LOCAL_SHA=$(git rev-parse HEAD)
  REMOTE_SHA=$(git rev-parse "$REMOTE/$BRANCH")

  if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
    log "No update needed."
    return
  fi

  log "Updating repo..."
  git reset --hard "$REMOTE/$BRANCH" --quiet

  if [ -f requirements.txt ]; then
    log "Installing dependencies..."
    pip install -r requirements.txt >/dev/null 2>&1 || true
  fi

  restart_gunicorn
}

updater_loop() {
  update_repo_if_needed
  while true; do
    sleep 86400
    update_repo_if_needed
  done
}

cleanup() {
  log "Shutting down..."
  [ -n "${UPDATER_PID:-}" ] && kill "$UPDATER_PID" 2>/dev/null || true
  stop_gunicorn
  exit 0
}

trap cleanup INT TERM

start_gunicorn
updater_loop &
UPDATER_PID=$!
log "Daily auto-update enabled."

# Start Cloudflare Tunnel
cloudflared tunnel run --protocol http2 <tunnel-name> > cloudflare.log 2>&1

cleanup
```