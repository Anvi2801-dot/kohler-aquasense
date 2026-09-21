# Kohler AquaSense OS — Handoff Document

**Project:** Kohler AquaSense OS  
**Deployment:** Pune International Airport (PNQ) — NITB Departure Zone 3  
**Stack:** Python 3.10 · FastAPI · Next.js 14 · Gemini 3.1 Flash Lite · scikit-learn  
**Author:** Anvi Singh Parihar  
**Date:** September 2026

---

## 1. What This Project Is

AquaSense OS is a real-time IoT anomaly detection and agentic maintenance dispatch system for Kohler commercial plumbing fixtures. It monitors 9 fixtures (4 sinks, 3 urinals, 2 stalls) across PNQ NITB Departure Zone 3, detects leaks and hygiene breaches using a four-algorithm analytics pipeline, and automatically generates AI-powered maintenance work orders via Gemini for AAI field technicians.

It is not a dashboard. It is a plumbing operating system — stateful, streaming, and agentic.

---

## 2. Repo Structure

```
kohler-aquasense-os/
├── backend/
│   ├── agent.py              # Gemini LLM agent — generates work order JSON
│   ├── analytics.py          # Core anomaly detection pipeline (no LLM)
│   ├── simulator.py          # Synthetic IoT telemetry generator
│   ├── main.py               # FastAPI backend — all API endpoints
│   ├── eval_agent.py         # Agent evaluation harness
│   ├── requirements.txt      # Python dependencies
│   └── app.py                # Entry point (alternate)
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Main dashboard — Executive + Technician views
│   │   ├── layout.tsx
│   │   └── globals.css
│   └── components/
│       ├── HeaderKPIs.tsx    # Top nav + KPI strip (water saved, cost, uptime)
│       ├── SpatialMap.tsx    # Restroom floor plan with live fixture cards
│       └── TechPortal.tsx    # Field technician work order queue
├── .env                      # API keys (not committed)
├── .env.example              # Template — copy to .env before running
├── Presentation_Deck.pdf
├── Prompts_Documentation.pdf
├── system_architecture_diagram.*
└── README.md
```

---

## 3. Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Gemini API key (get one at [aistudio.google.com](https://aistudio.google.com))

### Step 1 — Clone & configure environment

```bash
git clone <repo-url>
cd kohler-aquasense-os
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

### Step 2 — Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`  
Health check: `http://localhost:8000/health`

### Step 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`

> Both must be running simultaneously. The frontend polls the backend every 5 seconds.

---

## 4. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (soft) | Gemini API key for work order generation. App works without it — falls back to rule-based work orders. |

**The app never crashes on a missing key.** `agent.py` raises a `ValueError` which `main.py` catches at import time, setting `agent = None` and switching to the rule-based fallback in `generate_llm_work_order()`.

---

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/telemetry` | Fresh telemetry tick for all 9 fixtures |
| `GET` | `/api/telemetry/cached` | Last known state — no analytics reset |
| `POST` | `/api/simulate` | Inject anomaly mode (see below) |
| `GET/POST` | `/api/dispatch` | Generate work orders for active anomalies |
| `POST` | `/api/dispatch/complete` | Resolve a work order, restore fixture to NORMAL |
| `GET` | `/api/kpis` | Water saved, cost saved, uptime, active leaks |
| `GET` | `/health` | Health check |

### Simulation actions (`POST /api/simulate`)

```json
{ "action": "INJECT_LEAK" }         // Injects leak into a random sink
{ "action": "INJECT_LEAK", "fixture_id": "KOHLER_FAUCET_101" }  // Specific fixture
{ "action": "INJECT_HYGIENE" }      // Injects hygiene warning into a random urinal
{ "action": "FLIGHT_RUSH" }         // Traffic spike across ALL fixtures
{ "action": "RESET" }               // Restores all fixtures to NORMAL
```

---

## 6. The Analytics Pipeline

All anomaly detection runs in `analytics.py` — **no LLM calls here**.

```
IoT Tick → analyze_tick()
              ├── Rolling Z-score        (window=20, threshold=2.5)
              ├── Isolation Forest       (contamination=0.10, n_estimators=100)
              ├── Leak streak counter    (flow>0.25 LPM AND occupancy=0, streak>5)
              └── Dynamic Hygiene Index  (100 − 0.6×occupancy + 0.8×flush_count < 30)
```

Output anomaly codes: `ERR_CONTINUOUS_LEAK` · `ERR_FLOW_ZSCORE` · `ERR_ML_ANOMALY` · `HYGIENE_BREACH`

### Key configuration constants

```python
# analytics.py
ROLLING_WINDOW = 20
LEAK_FLOW_THRESHOLD = 0.25    # LPM
LEAK_TICKS_REQUIRED = 5       # consecutive ticks
Z_SCORE_THRESHOLD = 2.5
HYGIENE_BREACH_THRESHOLD = 30
```

---

## 7. The LLM Agent

`agent.py` calls Gemini 3.1 Flash Lite via the `google-genai` SDK with:

- `response_mime_type='application/json'` — SDK-level JSON enforcement
- `temperature=0.1` — near-deterministic output
- Embedded Kohler India part# reference table
- `K-UNKNOWN` fallback for uncertain part identification
- 7-field mandatory output schema with boundary constraints (`{` first, `}` last)

The agent is called from `main.py → generate_llm_work_order()`. If it fails for any reason, the function falls back to rule-based triage logic — **the dispatch endpoint never returns an error to the frontend**.

---

## 8. Key Formulas

```python
# Hygiene Score
hygiene_score = round(max(0.0, min(100.0, 100 - (0.6 * occupancy) + (0.8 * flush_count))), 2)

# Z-Score
z_score = (value - mean(history)) / stdev(history)

# Frontend Health Score
health_score = clamp(round(avg_hygiene * 0.6 + availability * 0.4 - leaks * 8), 0, 100)

# Water Efficiency
water_efficiency = clamp(100 - leaks * 3, 70, 100)

# Fleet Availability
fleet_availability = ((normal_count + hygiene_warning_count) / total_fixtures) * 100

# Water saved per resolved leak
water_saved = water_flow_lpm * 60  # ≈ 60 L/hr at LEAK mode flow rate of 1.0 LPM

# Cost saved
cost_saved_inr = total_water_saved_liters * 0.11  # PMC bulk utility tariff ₹0.11/L
```

---

## 9. Fixture Configuration

| Fixture ID | Name | Type | Part Number |
|---|---|---|---|
| KOHLER_FAUCET_101 | Departure Pier A - Sink 1 | Sink | K-72218-IN |
| KOHLER_FAUCET_102 | Departure Pier A - Sink 2 | Sink | K-72218-IN |
| KOHLER_FAUCET_103 | Departure Pier B - Sink 1 | Sink | K-72218-IN |
| KOHLER_FAUCET_104 | Departure Pier B - Sink 2 | Sink | K-72218-IN |
| KOHLER_URINAL_201 | Gate 5 Restroom - Urinal U1 | Urinal | K-4918-0 |
| KOHLER_URINAL_202 | Gate 5 Restroom - Urinal U2 | Urinal | K-4918-0 |
| KOHLER_URINAL_203 | Gate 5 Restroom - Urinal U3 | Urinal | K-4918-0 |
| KOHLER_STALL_301 | Gate 6 Restroom - Stall S1 | Stall | K-5401-ET |
| KOHLER_STALL_302 | Gate 6 Restroom - Stall S2 | Stall | K-5401-ET |

---

## 10. Known Issues & Limitations

| Issue | Impact | Status |
|---|---|---|
| Isolation Forest retrained from scratch on every tick | Performance degrades at scale; fine for 9 fixtures | Fixed by pre-training the model first |
| `reset_analytics_state()` accepts no fixture_id arg | `dispatch/complete` falls back to full reset | Workaround in place in main.py |
| `water_saved_lpm` variable name is misleading | Actually holds L/hr value (LPM × 60) | Variable name only — logic is correct |
| In-memory state only | All work orders and telemetry history lost on backend restart | By design for hackathon scope |
| `base_water_saved_liters = 1248.0` is hardcoded | KPI strip always starts at 1,248 L | Intentional simulation baseline |

---

## 11. Demo Script (For Judges)

1. Open `http://localhost:3000` — verify **System Online** badge and Health Score ~94–97
2. Click **Inject Solenoid Leak** — watch a sink card turn red on the floor map
3. Switch to **Field Technician Portal — Mohit** — work order appears with AI root cause
4. Click **Acknowledge & Complete** — fixture returns to green, water saved KPI increments
5. Click **Simulate Flight Landing Rush** — all fixtures go amber, Hygiene Compliance drops to ~1%
6. Click **Reset All Sensors** — system returns to normal operating state

---

## 12. What's Not Built (Future Scope)

- Persistent database (PostgreSQL) for work order history and audit trail
- Real Kohler fixture API integration (currently fully simulated)
- Push notifications / SMS dispatch to technicians
- Multi-zone support beyond Departure Zone 3
- Auth layer for Executive vs. Technician persona separation
- Mobile-responsive layout for field technician tablet use

---

## 13. Submission Artifacts

| File | Description |
|---|---|
| `Presentation_Deck.pdf` | Innovation pitch with system architecture and metrics |
| `Prompts_Documentation.pdf` | Four-module prompt engineering documentation |
| `HANDOFF.md` | This file |
| `system_architecture_diagram.*` | Pipeline architecture visual |
| `.env.example` | Environment variable template |

---
