#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AI DevOps Agent — local development startup
# Usage: ./start.sh
# ──────────────────────────────────────────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# ── Colour helpers ────────────────────────────────────────────
cyan="\033[1;36m"; green="\033[1;32m"; yellow="\033[1;33m"; reset="\033[0m"
info()  { echo -e "${cyan}[devops-agent]${reset} $*"; }
ok()    { echo -e "${green}[devops-agent]${reset} $*"; }
warn()  { echo -e "${yellow}[devops-agent]${reset} $*"; }

# ── .env check ───────────────────────────────────────────────
if [ ! -f "$BACKEND/.env" ]; then
  warn "backend/.env not found — copying from .env.example"
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  warn "Edit backend/.env and add your GEMINI_API_KEY"
fi

if [ ! -f "$FRONTEND/.env" ]; then
  cp "$FRONTEND/.env.example" "$FRONTEND/.env"
fi

# ── Python venv + deps ────────────────────────────────────────
info "Setting up Python virtual environment…"
cd "$BACKEND"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
ok "Backend dependencies ready"

# ── Start backend ─────────────────────────────────────────────
info "Starting FastAPI backend on http://localhost:8000 …"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ── Node deps ─────────────────────────────────────────────────
cd "$FRONTEND"
if [ ! -d "node_modules" ]; then
  info "Installing frontend dependencies (first run)…"
  npm install --legacy-peer-deps
fi
ok "Frontend dependencies ready"

# ── Start frontend ────────────────────────────────────────────
info "Starting React dev server on http://localhost:3000 …"
npm start &
FRONTEND_PID=$!

ok "Both services running!"
echo ""
echo -e "  Frontend  → ${cyan}http://localhost:3000${reset}"
echo -e "  API docs  → ${cyan}http://localhost:8000/docs${reset}"
echo -e "  WebSocket → ${cyan}ws://localhost:8000/ws${reset}"
echo ""
echo "Press Ctrl+C to stop all services."

# ── Shutdown handler ──────────────────────────────────────────
trap "info 'Shutting down…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
