# Kohler AquaSense OS

> Real-time IoT anomaly detection and agentic maintenance dispatch for Kohler commercial plumbing fixtures — deployed at Pune International Airport (PNQ) NITB Departure Zone 3.

---

![Python](https://img.shields.io/badge/Python_3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_3.1_Flash_Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)

## What It Does

AquaSense OS monitors 9 Kohler smart fixtures (sinks, urinals, stalls) across an airport terminal restroom in real time. When it detects a leak, hygiene breach, or flow anomaly, it automatically generates a structured AI maintenance work order — complete with root cause analysis, Kohler part number, and repair instructions — and dispatches it to the field technician's queue.

No manual log analysis. No delayed fault detection. Anomaly to work order in under 3 seconds.

---

## System Architecture

```
Simulator (simulator.py)
        │
        ▼
Analytics Engine (analytics.py)
  ├── Rolling Z-Score
  ├── Isolation Forest (ML)
  ├── Continuous Leak Detection
  └── Dynamic Hygiene Index
        │
        ▼
FastAPI Backend (main.py)
        │
        ├──→ Gemini 3.1 Flash Lite (agent.py)
        │         └── Work Order JSON
        │
        ▼
Next.js Dashboard (frontend/)
  ├── Executive View    — Health score, floor map, anomaly stream
  └── Technician Portal — Work order queue, acknowledge & complete
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, FastAPI, Uvicorn |
| Analytics | scikit-learn (Isolation Forest), statistics (Z-score) |
| LLM Agent | Gemini 3.1 Flash Lite via google-genai SDK |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Simulation | Custom synthetic IoT telemetry generator |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com)

### 1. Clone & configure

```bash
git clone <repo-url>
cd kohler-aquasense-os
cp .env.example .env
# Open .env and add your GEMINI_API_KEY
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

> **No API key?** The app still works — work orders fall back to rule-based generation. The AI dispatch path requires a key.

---

## Features

**Executive View**
- Live health score (0–100) with weighted hygiene, availability, and leak metrics
- Restroom spatial floor map with per-fixture status indicators
- Real-time anomaly stream table — auto-refreshes every 5 seconds
- KPIs: water saved (L), utility cost saved (₹), active fleet uptime (%)

**Field Technician Portal**
- AI-generated work orders with root cause analysis
- Kohler India part number recommendations
- Priority classification: CRITICAL / HIGH / ROUTINE
- Estimated water recovery per resolved fault
- One-click acknowledge & complete — restores fixture to normal

**Simulation Controls**
- Inject Solenoid Leak — triggers continuous flow anomaly on a sink
- Simulate Flight Landing Rush — traffic spike across all fixtures
- Reset All Sensors — returns system to normal operating state

---

## Detection Algorithms

| Algorithm | Method | Trigger |
|---|---|---|
| Continuous Leak | Streak counter | flow > 0.25 LPM AND occupancy = 0 for 5+ consecutive ticks |
| Flow Anomaly | Rolling Z-score | \|z\| ≥ 2.5 over 20-tick window |
| ML Anomaly | Isolation Forest | 10% contamination, feature vector [flow, flush, occupancy, pressure] |
| Hygiene Breach | Formula | `100 − (0.6 × occupancy) + (0.8 × flush_count) < 30` |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/telemetry` | Fresh telemetry for all 9 fixtures |
| GET | `/api/telemetry/cached` | Last known state (no reset) |
| POST | `/api/simulate` | Inject anomaly mode |
| GET | `/api/dispatch` | Get active work orders |
| POST | `/api/dispatch/complete` | Resolve a work order |
| GET | `/api/kpis` | Water saved, cost saved, uptime |
| GET | `/health` | Health check |

---

## Environment Variables

```bash
# .env
GEMINI_API_KEY=your_key_here
```

See `.env.example` for the template.

---

## Project Structure

```
kohler-aquasense-os/
├── backend/
│   ├── agent.py          # Gemini LLM agent
│   ├── analytics.py      # Anomaly detection pipeline
│   ├── simulator.py      # Synthetic telemetry generator
│   ├── main.py           # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx      # Main dashboard
│   │   └── globals.css
│   └── components/
│       ├── HeaderKPIs.tsx
│       ├── SpatialMap.tsx
│       └── TechPortal.tsx
├── .env.example
├── HANDOFF.md
├── Presentation_Deck.pdf
└── Prompts_Documentation.pdf
```

---

## Submission Artifacts

| File | Description |
|---|---|
| `Presentation_Deck.pdf` | Innovation pitch with metrics and architecture |
| `Prompts_Documentation.pdf` | Prompt engineering documentation — 4-module architecture |
| `HANDOFF.md` | Full technical handoff with setup, formulas, known issues |

---

*Built by Anvi Singh Parihar*