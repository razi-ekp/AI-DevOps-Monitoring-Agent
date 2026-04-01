# 🤖 AI DevOps Monitoring Agent

An autonomous, full-stack DevOps monitoring system that detects infrastructure anomalies, performs AI-driven root cause analysis, auto-heals services, and presents everything in a real-time dark-mode dashboard.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  Overview · Metrics · Logs · AI Insights · Incidents │
│  Auto-Healing · Alerts · Control Panel · AI Chatbot  │
└──────────────────────┬──────────────────────────────┘
           WebSocket + REST API
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │Simulator │  │ AI/RAG   │  │  Auto-Heal Engine  │ │
│  │(metrics, │  │(Gemini   │  │  (restart, scale,  │ │
│  │logs,     │  │ API)     │  │   rollback, flush) │ │
│  │incidents)│  └──────────┘  └────────────────────┘ │
│  └──────────┘                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │           In-memory State Store                  ││
│  │  metrics · logs · incidents · healing · alerts   ││
│  └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
devops-agent/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── metrics.py        # GET /api/metrics
│   │   │   ├── logs.py           # GET /api/logs
│   │   │   ├── incidents.py      # GET/POST /api/incidents
│   │   │   ├── ai.py             # POST /api/ai/analyze, GET /insights
│   │   │   ├── alerts.py         # GET /api/alerts
│   │   │   ├── healing.py        # GET/POST /api/healing
│   │   │   └── ws.py             # WebSocket /ws
│   │   └── core/
│   │       ├── state.py          # Shared in-memory store
│   │       ├── simulator.py      # Background data generator
│   │       └── broadcaster.py    # WebSocket fan-out
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.js                # Root layout
│   │   ├── index.css             # Design tokens + global styles
│   │   ├── hooks/
│   │   │   └── useDevOpsData.js  # WS + REST data hook
│   │   └── components/
│   │       ├── ui.js             # Shared primitives (Badge, Card…)
│   │       ├── dashboard/        # OverviewPanel, ControlPanel
│   │       ├── charts/           # MetricsChart, PodStatus
│   │       ├── logs/             # LogsViewer
│   │       ├── ai/               # AIInsightsPanel
│   │       ├── incidents/        # IncidentTimeline, HealingActionsPanel
│   │       └── alerts/           # AlertsPanel
│   ├── public/index.html
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
│
├── docker-compose.yml
├── start.sh                      # One-command local dev
└── README.md
```

---

## 🚀 Quick Start

### Option A — One command (local dev)

```bash
# 1. Clone / unzip the project
cd devops-agent

# 2. Add your Gemini API key
cp backend/.env.example backend/.env
echo "GEMINI_API_KEY=AIza..." >> backend/.env

# 3. Start everything
chmod +x start.sh && ./start.sh
```

Open **http://localhost:3000** — the dashboard loads instantly with live simulated data.

---

### Option B — Docker Compose (recommended for production)

```bash
# 1. Set your API key
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=AIza...

# 2. Build and start
docker-compose up --build

# Frontend → http://localhost:3000
# API docs  → http://localhost:8000/docs
```

---

### Option C — Manual (backend + frontend separately)

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
npm install --legacy-peer-deps
npm start
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (for AI features) | Gemini API key for AI analysis |
| `GEMINI_MODEL` | Optional | Gemini model name (default: `gemini-2.5-flash`) |
| `USE_REAL_METRICS` / `USE_REAL_LOGS` | Optional | Enable Prometheus/Loki ingestion instead of simulator output |
| `PROMETHEUS_URL` / `LOKI_URL` | Optional | Real telemetry provider endpoints |
| `USE_REAL_AUTOHEAL` | Optional | Enables real auto-heal execution path |
| `AUTOHEAL_EXECUTOR` | Optional | `dry-run` (default) or `kubectl` |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook for real alerts |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASS` | Optional | SMTP for email alerts |
| `REACT_APP_API_URL` | Frontend | Backend URL (default: `http://localhost:8000`) |
| `REACT_APP_WS_URL`  | Frontend | WebSocket URL (default: `ws://localhost:8000/ws`) |

> **Without `GEMINI_API_KEY`:** The dashboard still runs with simulated data. Deep analysis will return a warning message instead of real AI responses.

Real integration quick start:
1. Set `USE_REAL_METRICS=true` and `USE_REAL_LOGS=true`.
2. Set `PROMETHEUS_URL` and `LOKI_URL` to your telemetry endpoints.
3. Keep `AUTOHEAL_EXECUTOR=dry-run` while validating rules.
4. When ready, set `USE_REAL_AUTOHEAL=true`, `AUTOHEAL_EXECUTOR=kubectl`, and configure `AUTOHEAL_SERVICE_ALLOWLIST`.

Simulator tuning:
- `SIMULATOR_TICK_SECONDS` controls how often metrics update.
- `SIMULATOR_LOG_EVERY_N_TICKS` controls how often a log line is emitted.
- `SIMULATOR_INCIDENT_PROBABILITY` controls how often an error becomes an incident.

Real-data hookup guide:
- See [docs/REAL_DATA_SETUP.md](/c:/Users/MOHAMMED%20RAZI%20EKP/Quest/devops-agent/docs/REAL_DATA_SETUP.md) for the exact backend functions to replace when connecting Prometheus and Loki.

---

## 📊 Dashboard Features

| Panel | Description |
|---|---|
| **Overview** | System health, active incidents, CPU/Memory live stats |
| **Metrics** | Real-time area charts for CPU, Memory, Network, Disk |
| **Pod Status** | Kubernetes pod health, CPU/memory bars, restart counts |
| **Live Logs** | Streaming log viewer with service + severity filters |
| **AI Insights** | RAG-powered root cause analysis + recommended fixes |
| **Incident Timeline** | Chronological incident feed with severity + status |
| **Auto-Healing** | Actions taken, why, and validation result |
| **Alerts** | Real-time alert feed with Slack/Email channel status |
| **Control Panel** | Toggle auto-heal ON/OFF, trigger manual actions |
| **AI Insights** | Root-cause and remediation suggestions for high-severity incidents |

---

## 🔌 API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/api/metrics` | Last N metric snapshots |
| GET | `/api/metrics/summary` | System health summary |
| GET | `/api/metrics/pods` | Current pod statuses |
| GET | `/api/logs` | Filtered log entries |
| GET | `/api/incidents` | Incident list |
| POST | `/api/incidents/{id}/resolve` | Manually resolve incident |
| POST | `/api/ai/analyze` | Deep incident analysis |
| GET | `/api/ai/insights` | AI insight cards |
| GET | `/api/alerts` | Alert feed |
| GET | `/api/healing/actions` | Healing action history |
| POST | `/api/healing/toggle` | Enable/disable auto-heal |
| POST | `/api/healing/manual` | Trigger manual action |
| WS  | `/ws` | Real-time event stream |

Full interactive docs at **http://localhost:8000/docs**

---

## 🔁 Event Flow

```
Simulator generates anomaly
    │
    ▼
Incident created + broadcasted via WebSocket
    │
    ├─→ Frontend: red alert appears in Incident Timeline
    ├─→ Frontend: AI Insights panel fetches root cause
    ├─→ Alert fired (Slack / Email)
    │
    └─→ Auto-Heal Engine (if enabled)
            │
            ▼
        Action executed (restart / scale / rollback)
            │
            ▼
        Result broadcasted → dashboard updates
```

---

## 🧩 Extending the Project

### Connect real Prometheus
Replace `simulator.py` metric generation with calls to your Prometheus HTTP API:
```python
import httpx
resp = await httpx.get("http://prometheus:9090/api/v1/query", params={"query": "node_cpu_seconds_total"})
```

For a project-specific walkthrough, use:
- [docs/REAL_DATA_SETUP.md](/c:/Users/MOHAMMED%20RAZI%20EKP/Quest/devops-agent/docs/REAL_DATA_SETUP.md)

### Connect real Kubernetes
Use the `kubernetes` Python client:
```python
pip install kubernetes
from kubernetes import client, config
config.load_incluster_config()
v1 = client.CoreV1Api()
pods = v1.list_namespaced_pod("default")
```

### Add a vector DB for real RAG
```python
pip install chromadb
import chromadb
client = chromadb.Client()
collection = client.create_collection("runbooks")
```

---

## 🛡️ Safety Constraints

- Actions only execute when `auto_heal = true`
- Low-confidence decisions (< 50%) are escalated, not executed
- All healing actions are logged with `validated` flag
- Manual override always available via Control Panel

---

## 📄 License

MIT — free to use, modify, and deploy.


# For Running Full Project 
.\start-windows.ps1

