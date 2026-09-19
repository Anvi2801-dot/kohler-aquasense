"""
Kohler AquaSense OS
FastAPI Backend

Run:
    uvicorn main:app --reload --port 8000

Frontend:
    Next.js -> http://localhost:3000
Backend:
    FastAPI -> http://localhost:8000
"""

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from datetime import datetime, timezone
from typing import Literal, Any, Optional
import random
import time

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import numpy as np

def sanitize_numpy(obj):
    if isinstance(obj, dict):
        return {k: sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_numpy(v) for v in obj]
    elif hasattr(obj, "item"):  # Converts np.bool_, np.int64, np.float64 to Python native types
        return obj.item()
    return obj

# ============================================================
# EXISTING PROJECT MODULES
# ============================================================

from simulator import generate_telemetry_tick
from analytics import analyze_tick, reset_analytics_state

try:
    import agent
    print("✅ Successfully imported agent.py")
except Exception as e:
    import traceback
    print(f"❌ Failed to import agent.py: {e}")
    traceback.print_exc()
    agent = None


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Kohler AquaSense OS API",
    description="IoT Facility Intelligence Backend",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FIXTURE CONFIGURATION
# 4 Sinks + 3 Urinals + 2 Stalls = 9 Fixtures
# ============================================================

FIXTURES = [
    {
        "fixture_id": "KOHLER_FAUCET_101",
        "fixture_name": "Departure Pier A - Sink 1",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_102",
        "fixture_name": "Departure Pier A - Sink 2",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_103",
        "fixture_name": "Departure Pier B - Sink 1",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_104",
        "fixture_name": "Departure Pier B - Sink 2",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_URINAL_201",
        "fixture_name": "Gate 5 Restroom - Urinal U1",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_URINAL_202",
        "fixture_name": "Gate 5 Restroom - Urinal U2",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_URINAL_203",
        "fixture_name": "Gate 5 Restroom - Urinal U3",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_STALL_301",
        "fixture_name": "Gate 6 Restroom - Stall S1",
        "type": "Stall",
        "kohler_part_number": "K-5401-ET",
    },
    {
        "fixture_id": "KOHLER_STALL_302",
        "fixture_name": "Gate 6 Restroom - Stall S2",
        "type": "Stall",
        "kohler_part_number": "K-5401-ET",
    },
]


# ============================================================
# IN-MEMORY APPLICATION STATE
# ============================================================

fixture_modes: dict[str, str | None] = {
    fixture["fixture_id"]: None
    for fixture in FIXTURES
}

latest_state: dict[str, dict[str, Any]] = {}
telemetry_history: list[dict[str, Any]] = []
work_orders: list[dict[str, Any]] = []
pending_dispatches: set[str] = set()

system_started_at = time.time()

# Dynamic accumulation baselines
base_water_saved_liters = 1248.0
water_saved_accumulated = 0.0
WATER_COST_PER_LITER_INR = 0.11


# ============================================================
# REQUEST MODELS
# ============================================================

class SimulationRequest(BaseModel):
    action: Literal[
        "INJECT_LEAK",
        "INJECT_HYGIENE",
        "FLIGHT_RUSH",
        "RESET",
    ]
    fixture_id: Optional[str] = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def utc_now() -> str:
    """Return current UTC time as ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def get_fixture(fixture_id: str) -> dict[str, Any]:
    """Return fixture configuration."""
    for fixture in FIXTURES:
        if fixture["fixture_id"] == fixture_id:
            return fixture

    raise HTTPException(
        status_code=404,
        detail=f"Fixture {fixture_id} not found",
    )


def get_fixture_mode(fixture_id: str) -> str:
    """Convert internal mode to simulator-compatible mode."""
    return fixture_modes.get(fixture_id) or "NORMAL"


def calculate_status(analytics: dict[str, Any], mode: str) -> str:
    """Convert analytics results into frontend-friendly status."""
    if analytics.get("continuous_leak") or mode == "LEAK":
        return "LEAK"
    if analytics.get("hygiene_breach") or mode == "HYGIENE_WARNING" or mode == "TRAFFIC_SPIKE":
        return "HYGIENE_WARNING"
    return "NORMAL"


def build_fixture_state(
    fixture: dict[str, Any],
    tick: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any]:

    analytics = analysis.get("analytics", {})
    mode = get_fixture_mode(fixture["fixture_id"])
    status = calculate_status(analytics, mode)

    if status == "LEAK":
        severity = 0.95
    elif status == "HYGIENE_WARNING":
        severity = 0.75
    else:
        severity = 0.10

    return {
        "fixture_id": fixture["fixture_id"],
        "fixture_name": fixture["fixture_name"],
        "type": fixture["type"],
        "kohler_part_number": fixture["kohler_part_number"],
        "timestamp": tick.get("timestamp"),
        "water_flow_lpm": tick.get("water_flow_lpm", 0.0),
        "occupancy_count_10m": tick.get("occupancy_count_10m", 0),
        "flush_count_10m": tick.get("flush_count_10m", 0),
        "pressure_psi": tick.get("pressure_psi", 0.0),
        "diagnostic_code": tick.get("diagnostic_code", "OK"),
        "status": status,
        "severity": severity,
        "hygiene_score": analytics.get("hygiene_score", 100.0),
        "hygiene_breach": analytics.get("hygiene_breach", False),
        "continuous_leak": analytics.get("continuous_leak", False),
        "ml_anomaly": analytics.get("ml_anomaly", False),
        "anomaly_codes": analysis.get("anomaly_codes", []),
    }


def process_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    fixture_id = fixture["fixture_id"]
    mode = get_fixture_mode(fixture_id)

    tick = generate_telemetry_tick(
        zone_id="PNQ_NITB_DEPARTURE_ZONE_3",
        fixture_id=fixture_id,
        anomaly_mode=mode,
    )

    analysis = analyze_tick(tick)
    state = build_fixture_state(fixture, tick, analysis)
    latest_state[fixture_id] = state

    telemetry_history.append(
        {
            **tick,
            "status": state["status"],
            "hygiene_score": state["hygiene_score"],
            "anomaly_codes": state["anomaly_codes"],
        }
    )

    if len(telemetry_history) > 500:
        del telemetry_history[:-500]

    return state


def refresh_all_fixtures() -> list[dict[str, Any]]:
    states = []
    for fixture in FIXTURES:
        state = process_fixture(fixture)
        states.append(state)
    return states


def reset_system_state() -> None:
    global water_saved_accumulated

    for fixture_id in fixture_modes:
        fixture_modes[fixture_id] = None

    latest_state.clear()
    telemetry_history.clear()
    work_orders.clear()
    pending_dispatches.clear()

    reset_analytics_state()
    water_saved_accumulated = 0.0


# ============================================================
# GEMINI / AGENT ADAPTER
# ============================================================

def generate_llm_work_order(fixture_state: dict[str, Any]) -> dict[str, Any]:
    fixture_id = fixture_state["fixture_id"]
    anomaly_codes = fixture_state.get("anomaly_codes", [])

    if agent is not None:
        possible_functions = [
            "generate_work_order",
            "dispatch_work_order",
            "dispatch_anomaly",
            "diagnose_anomaly",
            "generate_diagnostic",
        ]

        for function_name in possible_functions:
            function = getattr(agent, function_name, None)

            if callable(function):
                try:
                    clean_state = sanitize_numpy(fixture_state)
                    result = function(clean_state)

                    if isinstance(result, dict):
                        root_cause = result.get(
                            "root_cause_analysis",
                            result.get("root_cause", "Detected abnormal fixture telemetry"),
                        )

                        water_saved = float(
                            result.get(
                                "estimated_water_saved_lph",
                                result.get(
                                    "water_saved_lpm",
                                    round(fixture_state["water_flow_lpm"] * 60, 1),
                                ),
                            )
                        )

                        return {
                            "ticket_id": result.get(
                                "ticket_id",
                                f"WO-{fixture_id}-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
                            ),
                            "fixture_id": result.get("fixture_id", fixture_id),
                            "priority": result.get("priority", "HIGH"),
                            "root_cause": root_cause,
                            "recommended_action": result.get(
                                "recommended_action",
                                "Inspect fixture and water supply assembly",
                            ),
                            "kohler_part_number": result.get(
                                "kohler_part_number",
                                fixture_state["kohler_part_number"],
                            ),
                            "water_saved_lpm": water_saved,
                        }

                except Exception as e:
                    import traceback
                    print(f"AGENT CALL FAILED FOR {fixture_id}: {e}")
                    traceback.print_exc()

    # Fallback reasoning
    if "ERR_CONTINUOUS_LEAK" in anomaly_codes or fixture_state.get("status") == "LEAK":
        root_cause = "Continuous water flow detected while occupancy remained at zero."
        recommended_action = "Inspect the faucet/flush valve cartridge, solenoid and supply connection immediately."
        priority = "CRITICAL"
    elif "HYGIENE_BREACH" in anomaly_codes or fixture_state.get("status") == "HYGIENE_WARNING":
        root_cause = "Dynamic hygiene index fell below the facility safety threshold."
        recommended_action = "Inspect fixture usage, sanitation conditions and cleaning schedule."
        priority = "HIGH"
    else:
        root_cause = "Machine-learning analytics detected an unusual fixture telemetry pattern."
        recommended_action = "Inspect fixture diagnostics and verify flow, pressure and usage behavior."
        priority = "HIGH"

    return {
        "ticket_id": f"WO-{fixture_id}-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}",
        "fixture_id": fixture_id,
        "priority": priority,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "kohler_part_number": fixture_state["kohler_part_number"],
        "water_saved_lpm": round(fixture_state["water_flow_lpm"] * 60, 1),
    }


# ============================================================
# API: GET TELEMETRY
# ============================================================

@app.get("/api/telemetry")
def get_telemetry():
    states = refresh_all_fixtures()
    return sanitize_numpy({
        "timestamp": utc_now(),
        "facility": "Pune International Airport (PNQ)- NITB Departure Zone 3",
        "fixture_count": len(states),
        "fixtures": states,
    })


@app.get("/api/telemetry/cached")
def get_cached_telemetry():
    if not latest_state:
        refresh_all_fixtures()

    return sanitize_numpy({
        "timestamp": utc_now(),
        "facility": "Pune International Airport (PNQ)- NITB Departure Zone 3",
        "fixture_count": len(latest_state),
        "fixtures": list(latest_state.values()),
    })


# ============================================================
# API: SIMULATE
# ============================================================

@app.post("/api/simulate")
def simulate_action(request: SimulationRequest):
    action = request.action
    target_fixture = request.fixture_id

    if action == "INJECT_LEAK":
        if not target_fixture or target_fixture not in fixture_modes:
            target_fixture = random.choice([f["fixture_id"] for f in FIXTURES if f["type"] == "Sink"])

        fixture_modes[target_fixture] = "LEAK"
        refresh_all_fixtures()

        return {
            "success": True,
            "action": action,
            "message": f"Continuous leak injected into {target_fixture}",
            "fixture_id": target_fixture,
        }

    if action == "INJECT_HYGIENE":
        if not target_fixture or target_fixture not in fixture_modes:
            target_fixture = random.choice([f["fixture_id"] for f in FIXTURES if f["type"] == "Urinal"])

        fixture_modes[target_fixture] = "HYGIENE_WARNING"
        refresh_all_fixtures()

        return {
            "success": True,
            "action": action,
            "message": f"Hygiene warning injected into {target_fixture}",
            "fixture_id": target_fixture,
        }

    if action == "FLIGHT_RUSH":
        for fid in fixture_modes:
            fixture_modes[fid] = "TRAFFIC_SPIKE"
        refresh_all_fixtures()

        return {
            "success": True,
            "action": action,
            "message": "Flight rush simulation activated across all commercial fixtures.",
            "affected_fixtures": len(fixture_modes),
        }

    if action == "RESET":
        reset_system_state()
        refresh_all_fixtures()
        return {
            "success": True,
            "action": action,
            "message": "AquaSense OS returned to normal operating state.",
        }

    raise HTTPException(status_code=400, detail="Unsupported simulation action")


# ============================================================
# API: DISPATCH
# ============================================================

@app.get("/api/dispatch")
@app.post("/api/dispatch")
def dispatch_anomalies():
    if not latest_state:
        refresh_all_fixtures()

    anomalies = [
        state for state in latest_state.values()
        if state["status"] in ["LEAK", "HYGIENE_WARNING"]
        or "ERR_CONTINUOUS_LEAK" in state.get("anomaly_codes", [])
    ]

    for state in anomalies:
        fixture_id = state["fixture_id"]

        existing = next((o for o in work_orders if o["fixture_id"] == fixture_id), None)
        if existing:
            continue

        if fixture_id in pending_dispatches:
            continue

        try:
            pending_dispatches.add(fixture_id)
            work_order = generate_llm_work_order(state)
            if work_order:
                work_orders.append(work_order)
        finally:
            pending_dispatches.discard(fixture_id)

    return sanitize_numpy({
        "success": True,
        "dispatched_at": utc_now(),
        "active_anomalies": len(anomalies),
        "work_orders": work_orders,
    })


# ============================================================
# API: DISPATCH COMPLETE
# ============================================================

@app.post("/api/dispatch/complete")
def complete_work_order(payload: dict):
    global work_orders
    global water_saved_accumulated

    ticket_id = payload.get("ticket_id")
    fixture_id = payload.get("fixture_id")

    if not ticket_id or not fixture_id:
        raise HTTPException(
            status_code=400,
            detail="Both ticket_id and fixture_id are required.",
        )

    # Accumulate water saved metrics upon ticket resolution
    completed_order = next((o for o in work_orders if o.get("ticket_id") == ticket_id), None)
    if completed_order:
        saved_rate = completed_order.get("water_saved_lpm", 60.0)
        water_saved_accumulated += saved_rate

    if fixture_id in fixture_modes:
        fixture_modes[fixture_id] = None

    try:
        reset_analytics_state(fixture_id)
    except TypeError:
        try:
            reset_analytics_state()
        except Exception:
            pass

    work_orders = [wo for wo in work_orders if wo.get("ticket_id") != ticket_id]
    refresh_all_fixtures()

    return sanitize_numpy({
        "success": True,
        "ticket_id": ticket_id,
        "fixture_id": fixture_id,
        "status": "COMPLETED",
        "message": f"Fixture {fixture_id} restored to normal operation.",
    })


# ============================================================
# API: KPIs
# ============================================================

@app.get("/api/kpis")
def get_kpis():
    if not latest_state:
        refresh_all_fixtures()

    active_leaks = sum(
        1 for state in latest_state.values()
        if state["status"] in ["LEAK", "HYGIENE_WARNING"]
    )

    total_fixtures = len(FIXTURES)
    uptime = round(((total_fixtures - active_leaks) / total_fixtures) * 100, 1)

    total_water_saved = base_water_saved_liters + water_saved_accumulated
    total_cost_saved = round(total_water_saved * WATER_COST_PER_LITER_INR, 2)

    return {
        "total_water_saved_liters": round(total_water_saved, 1),
        "cost_saved_inr": total_cost_saved,
        "active_leaks_count": active_leaks,
        "system_uptime_percent": uptime,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Kohler AquaSense OS",
        "status": "ONLINE",
        "backend": "FastAPI",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": utc_now(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)