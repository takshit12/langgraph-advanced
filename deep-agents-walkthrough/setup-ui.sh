#!/usr/bin/env bash
#
# setup-ui.sh — clone, configure, and launch the deep-agents-ui so you can watch
# the competitive-analysis agent work live (plan, files, sub-agents).
#
# Usage:
#   ./setup-ui.sh                # set up (if needed) and start the UI on :3000
#   ./setup-ui.sh --setup-only   # clone + install + write .env.local, but don't start
#
# Prereqs: git, Node 20+ (https://nodejs.org). Yarn is used if present; otherwise
# the bundled `corepack yarn` or `npm` is used as a fallback.
#
# You also need the agent's LangGraph server running in another terminal:
#   cd competitive_analysis_agent && uv run langgraph dev
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="$HERE/deep-agents-ui"
ENV_FILE="$HERE/.env"
UI_REPO="https://github.com/langchain-ai/deep-agents-ui.git"

DEPLOYMENT_URL="http://127.0.0.1:2024"
ASSISTANT_ID="competitive_analysis_agent"

SETUP_ONLY=0
[ "${1:-}" = "--setup-only" ] && SETUP_ONLY=1

# --- pick a package manager (prefer yarn; the UI ships a yarn.lock) -----------
pm_install() {
  if command -v yarn >/dev/null 2>&1; then yarn install
  elif command -v corepack >/dev/null 2>&1; then corepack yarn install
  else echo "(no yarn/corepack found — using npm)"; npm install
  fi
}
pm_dev() {
  if command -v yarn >/dev/null 2>&1; then yarn dev
  elif command -v corepack >/dev/null 2>&1; then corepack yarn dev
  else npm run dev
  fi
}

# --- 1. clone (or update) the UI ---------------------------------------------
if [ ! -d "$UI_DIR/.git" ]; then
  echo "==> Cloning deep-agents-ui into $UI_DIR"
  git clone "$UI_REPO" "$UI_DIR"
else
  echo "==> deep-agents-ui already present — pulling latest"
  git -C "$UI_DIR" pull --ff-only || echo "   (skipped pull; local changes present)"
fi

# --- 2. install deps (skip if already installed) -----------------------------
cd "$UI_DIR"
if [ -d node_modules ]; then
  echo "==> Dependencies already installed (delete deep-agents-ui/node_modules to force a reinstall)"
else
  echo "==> Installing dependencies (this can take a few minutes)"
  pm_install
fi

# --- 3. write .env.local with the optional LangSmith key from ../.env ---------
if [ -f "$ENV_FILE" ]; then
  LS_KEY="$(grep -E '^LANGSMITH_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- || true)"
  if [ -n "${LS_KEY:-}" ]; then
    printf 'NEXT_PUBLIC_LANGSMITH_API_KEY=%s\n' "$LS_KEY" > "$UI_DIR/.env.local"
    echo "==> Wrote deep-agents-ui/.env.local with your LangSmith key"
  fi
fi

# --- 4. tell the user exactly how to connect ---------------------------------
cat <<EOF

────────────────────────────────────────────────────────────────────────
 deep-agents-ui is ready.

 1) Make sure the agent server is running (in another terminal):
      cd "$HERE/competitive_analysis_agent" && uv run langgraph dev

 2) Open the UI:  http://localhost:3000

 3) In the UI's settings dialog, enter:
      Deployment URL : $DEPLOYMENT_URL
      Assistant ID   : $ASSISTANT_ID
      LangSmith Key  : (optional — already in .env.local if you set one)

 These save to your browser, so you only enter them once.
────────────────────────────────────────────────────────────────────────
EOF

# --- 5. start the dev server (unless --setup-only) ---------------------------
if [ "$SETUP_ONLY" -eq 1 ]; then
  echo "Setup complete. Start it later with:  cd deep-agents-ui && yarn dev"
else
  echo "==> Starting the UI on http://localhost:3000  (Ctrl-C to stop)"
  pm_dev
fi
