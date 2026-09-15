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

from datetime import datetime, timezone
from typing import Literal, Any
import random
import time

from fastapi import FastAPI, HTTPException
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

# Try to import your existing Gemini/LLM agent.
# The adapter below can be changed to match your exact agent.py.
try:
    import agent
except ImportError:
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
        "fixture_name": "Sink Bank A1",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_102",
        "fixture_name": "Sink Bank A2",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_103",
        "fixture_name": "Sink Bank B1",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_FAUCET_104",
        "fixture_name": "Sink Bank B2",
        "type": "Sink",
        "kohler_part_number": "K-72218-IN",
    },
    {
        "fixture_id": "KOHLER_URINAL_201",
        "fixture_name": "Urinal Row U1",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_URINAL_202",
        "fixture_name": "Urinal Row U2",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_URINAL_203",
        "fixture_name": "Urinal Row U3",
        "type": "Urinal",
        "kohler_part_number": "K-4918-0",
    },
    {
        "fixture_id": "KOHLER_STALL_301",
        "fixture_name": "Stall S1",
        "type": "Stall",
        "kohler_part_number": "K-5401-ET",
    },
    {
        "fixture_id": "KOHLER_STALL_302",
        "fixture_name": "Stall S2",
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

system_started_at = time.time()

# Demo baseline values.
total_water_saved_liters = 1248.0
cost_saved_usd = 18.72


# ============================================================
# REQUEST MODELS
# ============================================================

class SimulationRequest(BaseModel):
    action: Literal[
        "INJECT_LEAK",
        "FLIGHT_RUSH",
        "RESET",
    ]


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
    """
    Convert internal mode to simulator-compatible mode.
    """
    return fixture_modes.get(fixture_id) or "NORMAL"


def calculate_status(
    analytics: dict[str, Any],
    mode: str,
) -> str:
    """
    Convert analytics results into frontend-friendly status.
    """

    # Active continuous leak has highest priority.
    if analytics.get("continuous_leak"):
        return "LEAK"

    # Explicit leak mode is also shown as LEAK.
    if mode == "LEAK":
        return "LEAK"

    # Hygiene breach.
    if analytics.get("hygiene_breach"):
        return "HYGIENE_WARNING"

    return "NORMAL"


def build_fixture_state(
    fixture: dict[str, Any],
    tick: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any]:

    analytics = analysis.get("analytics", {})

    mode = get_fixture_mode(
        fixture["fixture_id"]
    )

    status = calculate_status(
        analytics,
        mode,
    )

    return {
        "fixture_id": fixture["fixture_id"],
        "fixture_name": fixture["fixture_name"],
        "type": fixture["type"],
        "kohler_part_number": fixture["kohler_part_number"],

        "timestamp": tick.get("timestamp"),

        "water_flow_lpm": tick.get(
            "water_flow_lpm",
            0.0,
        ),

        "occupancy_count_10m": tick.get(
            "occupancy_count_10m",
            0,
        ),

        "flush_count_10m": tick.get(
            "flush_count_10m",
            0,
        ),

        "pressure_psi": tick.get(
            "pressure_psi",
            0.0,
        ),

        "diagnostic_code": tick.get(
            "diagnostic_code",
            "OK",
        ),

        "status": status,

        "hygiene_score": analytics.get(
            "hygiene_score",
            100.0,
        ),

        "hygiene_breach": analytics.get(
            "hygiene_breach",
            False,
        ),

        "continuous_leak": analytics.get(
            "continuous_leak",
            False,
        ),

        "ml_anomaly": analytics.get(
            "ml_anomaly",
            False,
        ),

        "anomaly_codes": analysis.get(
            "anomaly_codes",
            [],
        ),
    }


def process_fixture(
    fixture: dict[str, Any],
) -> dict[str, Any]:

    fixture_id = fixture["fixture_id"]

    mode = get_fixture_mode(fixture_id)

    tick = generate_telemetry_tick(
        zone_id="AIRPORT_TERMINAL_RESTROOM",
        fixture_id=fixture_id,
        anomaly_mode=mode,
    )

    analysis = analyze_tick(tick)

    state = build_fixture_state(
        fixture,
        tick,
        analysis,
    )

    latest_state[fixture_id] = state

    telemetry_history.append(
        {
            **tick,
            "status": state["status"],
            "hygiene_score": state["hygiene_score"],
            "anomaly_codes": state["anomaly_codes"],
        }
    )

    # Keep memory bounded.
    if len(telemetry_history) > 500:
        del telemetry_history[:-500]

    return state


def refresh_all_fixtures() -> list[dict[str, Any]]:
    """
    Generate one telemetry tick for every fixture.
    """

    states = []

    for fixture in FIXTURES:
        state = process_fixture(fixture)
        states.append(state)

    return states


def reset_system_state() -> None:
    """
    Reset all simulated faults and analytics state.
    """

    global total_water_saved_liters
    global cost_saved_usd

    for fixture_id in fixture_modes:
        fixture_modes[fixture_id] = None

    latest_state.clear()
    telemetry_history.clear()
    work_orders.clear()

    reset_analytics_state()

    total_water_saved_liters = 1248.0
    cost_saved_usd = 18.72


# ============================================================
# GEMINI / AGENT ADAPTER
# ============================================================

def generate_llm_work_order(
    fixture_state: dict[str, Any],
) -> dict[str, Any]:
    """
    Call agent.py if a compatible dispatcher exists.

    Expected final work-order structure:

    {
        "ticket_id": "...",
        "fixture_id": "...",
        "priority": "...",
        "root_cause": "...",
        "recommended_action": "...",
        "kohler_part_number": "...",
        "water_saved_lph": 0.0
    }
    """

    fixture_id = fixture_state["fixture_id"]
    anomaly_codes = fixture_state.get(
        "anomaly_codes",
        [],
    )

    # --------------------------------------------------------
    # Attempt to use the existing agent.py
    # --------------------------------------------------------

    if agent is not None:

        possible_functions = [
            "generate_work_order",
            "dispatch_work_order",
            "dispatch_anomaly",
            "diagnose_anomaly",
            "generate_diagnostic",
        ]

        for function_name in possible_functions:

            function = getattr(
                agent,
                function_name,
                None,
            )

            if callable(function):

                try:

                    result = function(
                        fixture_state
                    )

                    if isinstance(result, dict):

                        return {
                            "ticket_id": result.get(
                                "ticket_id",
                                f"WO-{random.randint(10000, 99999)}",
                            ),

                            "fixture_id": result.get(
                                "fixture_id",
                                fixture_id,
                            ),

                            "priority": result.get(
                                "priority",
                                "HIGH",
                            ),

                            "root_cause": result.get(
                                "root_cause",
                                "Detected abnormal fixture telemetry",
                            ),

                            "recommended_action": result.get(
                                "recommended_action",
                                "Inspect fixture and water supply assembly",
                            ),

                            "kohler_part_number": result.get(
                                "kohler_part_number",
                                fixture_state[
                                    "kohler_part_number"
                                ],
                            ),

                            "water_saved_lph": float(
                                result.get(
                                    "water_saved_lph",
                                    fixture_state[
                                        "water_flow_lpm"
                                    ] * 60,
                                )
                            ),
                        }

                except Exception:
                    # If Gemini/API call fails, continue with
                    # deterministic fallback below.
                    pass

    # --------------------------------------------------------
    # Deterministic fallback
    # --------------------------------------------------------

    if "ERR_CONTINUOUS_LEAK" in anomaly_codes:

        root_cause = (
            "Continuous water flow detected while "
            "occupancy remained at zero."
        )

        recommended_action = (
            "Inspect the faucet/flush valve cartridge, "
            "solenoid and supply connection immediately."
        )

        priority = "CRITICAL"

    elif "HYGIENE_BREACH" in anomaly_codes:

        root_cause = (
            "Dynamic hygiene index fell below the "
            "facility safety threshold."
        )

        recommended_action = (
            "Inspect fixture usage, sanitation conditions "
            "and cleaning schedule."
        )

        priority = "HIGH"

    else:

        root_cause = (
            "Machine-learning analytics detected an "
            "unusual fixture telemetry pattern."
        )

        recommended_action = (
            "Inspect fixture diagnostics and verify "
            "flow, pressure and usage behavior."
        )

        priority = "MEDIUM"

    return {
        "ticket_id": (
            f"WO-{random.randint(10000, 99999)}"
        ),

        "fixture_id": fixture_id,

        "priority": priority,

        "root_cause": root_cause,

        "recommended_action": recommended_action,

        "kohler_part_number": fixture_state[
            "kohler_part_number"
        ],

        "water_saved_lph": round(
            fixture_state["water_flow_lpm"] * 60,
            2,
        ),
    }


# ============================================================
# API: GET TELEMETRY
# ============================================================

@app.get("/api/telemetry")
def get_telemetry():
    """
    Return current state of all 9 commercial fixtures.
    """

    states = refresh_all_fixtures()

    # Wrap the response with sanitize_numpy to convert np.bool_ / np types
    return sanitize_numpy({
        "timestamp": utc_now(),

        "facility": "Airport Terminal Restroom",

        "fixture_count": len(states),

        "fixtures": states,
    })


# ============================================================
# API: SIMULATE
# ============================================================

@app.post("/api/simulate")
def simulate_action(request: SimulationRequest):
    """
    Trigger a system simulation.

    INJECT_LEAK:
        Inject continuous leak into one sink.

    FLIGHT_RUSH:
        Simulate high-footfall traffic across all fixtures.

    RESET:
        Restore normal operation.
    """

    action = request.action

    # --------------------------------------------------------
    # INJECT LEAK
    # --------------------------------------------------------

    if action == "INJECT_LEAK":

        # First sink is selected as demonstration fault.
        target_fixture = "KOHLER_FAUCET_101"

        fixture_modes[target_fixture] = "LEAK"

        return {
            "success": True,
            "action": action,
            "message": (
                f"Continuous leak injected into "
                f"{target_fixture}"
            ),
            "fixture_id": target_fixture,
        }

    # --------------------------------------------------------
    # FLIGHT RUSH
    # --------------------------------------------------------

    if action == "FLIGHT_RUSH":

        for fixture_id in fixture_modes:

            fixture_modes[fixture_id] = (
                "TRAFFIC_SPIKE"
            )

        return {
            "success": True,
            "action": action,
            "message": (
                "Flight rush simulation activated "
                "across all commercial fixtures."
            ),
            "affected_fixtures": len(
                fixture_modes
            ),
        }

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if action == "RESET":

        reset_system_state()

        return {
            "success": True,
            "action": action,
            "message": (
                "AquaSense OS returned to normal "
                "operating state."
            ),
        }

    raise HTTPException(
        status_code=400,
        detail="Unsupported simulation action",
    )


# ============================================================
# API: DISPATCH
# ============================================================

@app.get("/api/dispatch")
@app.post("/api/dispatch")
def dispatch_anomalies():
    """
    Generate AI work orders for every currently active anomaly.
    Supports both GET (for initial fetch/polling) and POST (for triggering dispatch).
    """

    # Generate fresh telemetry before dispatching.
    states = refresh_all_fixtures()

    anomalies = [
        state
        for state in states
        if state["status"] != "NORMAL"
        or len(state["anomaly_codes"]) > 0
    ]

    generated_orders = []

    for state in anomalies:

        # Avoid duplicate active tickets.
        existing = next(
            (
                order
                for order in work_orders
                if order["fixture_id"] == state["fixture_id"]
            ),
            None,
        )

        if existing:
            generated_orders.append(existing)
            continue

        work_order = generate_llm_work_order(state)
        work_orders.append(work_order)
        generated_orders.append(work_order)

    # Return active work orders (including manually created or persisted ones)
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
    """
    Acknowledge and clear an active work order, resetting 
    the targeted fixture state back to NORMAL.
    """
    global work_orders

    ticket_id = payload.get("ticket_id")
    fixture_id = payload.get("fixture_id")

    if not ticket_id or not fixture_id:
        raise HTTPException(
            status_code=400,
            detail="Both ticket_id and fixture_id are required.",
        )

    # 1. Reset internal fixture mode back to None (NORMAL)
    if fixture_id in fixture_modes:
        fixture_modes[fixture_id] = None

    # 2. Reset analytics engine state safely
    try:
        reset_analytics_state(fixture_id)
    except TypeError:
        try:
            reset_analytics_state()
        except Exception:
            pass

    # 3. Remove work order from active list
    work_orders = [
        wo for wo in work_orders if wo.get("ticket_id") != ticket_id
    ]

    # 4. Refresh telemetry tick to clear latest_state immediately
    refresh_all_fixtures()

    # Wrap the return with sanitize_numpy
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
    """
    Return executive-level system KPIs.
    """

    # Use latest state where available.
    # If the system has not been queried yet,
    # create an initial state.
    if not latest_state:
        refresh_all_fixtures()

    active_leaks = sum(
        1
        for state in latest_state.values()
        if state["status"] == "LEAK"
    )

    uptime = 99.7

    return {
        "total_water_saved_liters": round(
            total_water_saved_liters,
            2,
        ),

        "cost_saved_usd": round(
            cost_saved_usd,
            2,
        ),

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


# ============================================================
# UVICORN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )