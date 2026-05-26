#!/usr/bin/env bash
# html-response · idempotent server starter.
#
# Safe to call every turn:
#   - if our server is already up on port 4747, exits 0 immediately
#   - if the port is held by SOMEONE ELSE, exits 2 with a clear error
#   - otherwise spawns serve.py in the background (detached, nohup, dev/null'd)
#     and waits for it to bind (up to ~4 seconds)
#
# Prints the URL on stdout on success. Errors go to stderr.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$SKILL_DIR/state"
PID_FILE="$STATE_DIR/server.pid"
LOG_FILE="$STATE_DIR/server.log"
HOST="127.0.0.1"
PORT="4747"
URL="http://$HOST:$PORT/"

mkdir -p "$STATE_DIR/responses"

# Probe: is something serving our /version endpoint with our JSON shape?
ours_running() {
  local body
  body="$(curl -sS --max-time 1 "http://$HOST:$PORT/version" 2>/dev/null || true)"
  [[ "$body" == *'"latest"'* ]]
}

# Fast path: existing healthy server
if ours_running; then
  echo "$URL"
  exit 0
fi

# Port held by something foreign?
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "html-response: port $PORT is held by a non-html-response process. Free it or pick another port in serve.py." >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  exit 2
fi

# Clean stale PID
if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    : # still alive — let the readiness loop confirm
  else
    rm -f "$PID_FILE"
  fi
fi

# Launch detached. nohup + setsid-style trick on macOS = disown + redirects.
nohup python3 "$SKILL_DIR/serve.py" </dev/null >>"$LOG_FILE" 2>&1 &
disown $! || true

# Wait for bind (up to ~4s, polling every 200ms)
for i in $(seq 1 20); do
  if ours_running; then
    echo "$URL"
    exit 0
  fi
  sleep 0.2
done

echo "html-response: server did not bind within 4s — check $LOG_FILE" >&2
tail -n 20 "$LOG_FILE" >&2 || true
exit 1
