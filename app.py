
"""
Kohler AquaSense OS
-------------------
Streamlit Multi-Persona Dashboard

Tab 1:
    Executive View - Facility Head

Tab 2:
    Field Technician Portal - Marcus

Dependencies:
    streamlit
    plotly
    pandas
    simulator.py
    analytics.py
"""

import random
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.simulator import generate_telemetry_tick
from backend.analytics import analyze_tick, reset_analytics_state


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Kohler AquaSense OS",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application background */
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #334155;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #38bdf8;
    }

    /* Main headings */
    h1, h2, h3 {
        color: #38bdf8 !important;
    }

    /* KPI cards */
    .kpi-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
        min-height: 125px;
    }

    .kpi-title {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    .kpi-value {
        color: #f8fafc;
        font-size: 32px;
        font-weight: 700;
        margin-top: 8px;
    }

    /* Generic dashboard cards */
    .dashboard-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
    }

    /* Card headers */
    .card-header {
        color: #38bdf8;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    /* Status badges */
    .status-normal {
        color: #22c55e;
        font-weight: 700;
    }

    .status-warning {
        color: #f59e0b;
        font-weight: 700;
    }

    .status-critical {
        color: #ef4444;
        font-weight: 700;
    }

    /* Technician work-order cards */
    .work-order {
        background-color: #1e293b;
        border: 1px solid #475569;
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .work-order-title {
        color: #f8fafc;
        font-size: 18px;
        font-weight: 700;
    }

    .work-order-label {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .work-order-value {
        color: #e2e8f0;
        font-size: 15px;
        margin-bottom: 8px;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FACILITY CONFIGURATION
# ============================================================

FIXTURES = [
    {
        "id": "KOHLER_FAUCET_101",
        "name": "Sink Bank A1",
        "type": "Sink",
        "part": "K-72218-IN",
        "x": 2,
        "y": 8,
    },
    {
        "id": "KOHLER_FAUCET_102",
        "name": "Sink Bank A2",
        "type": "Sink",
        "part": "K-72218-IN",
        "x": 4,
        "y": 8,
    },
    {
        "id": "KOHLER_FAUCET_103",
        "name": "Sink Bank B1",
        "type": "Sink",
        "part": "K-72218-IN",
        "x": 12,
        "y": 8,
    },
    {
        "id": "KOHLER_URINAL_201",
        "name": "Urinal Row U1",
        "type": "Urinal",
        "part": "K-4918-0",
        "x": 3,
        "y": 3,
    },
    {
        "id": "KOHLER_URINAL_202",
        "name": "Urinal Row U2",
        "type": "Urinal",
        "part": "K-4918-0",
        "x": 6,
        "y": 3,
    },
    {
        "id": "KOHLER_URINAL_203",
        "name": "Urinal Row U3",
        "type": "Urinal",
        "part": "K-4918-0",
        "x": 9,
        "y": 3,
    },
    {
        "id": "KOHLER_STALL_301",
        "name": "Stall S1",
        "type": "Stall",
        "part": "K-5401-ET",
        "x": 14,
        "y": 3,
    },
    {
        "id": "KOHLER_STALL_302",
        "name": "Stall S2",
        "type": "Stall",
        "part": "K-5401-ET",
        "x": 14,
        "y": 6,
    },
    {
        "id": "KOHLER_STALL_303",
        "name": "Stall S3",
        "type": "Stall",
        "part": "K-5401-ET",
        "x": 14,
        "y": 9,
    },
]


# ============================================================
# SESSION STATE
# ============================================================

if "telemetry" not in st.session_state:
    st.session_state.telemetry = []

if "anomalies" not in st.session_state:
    st.session_state.anomalies = []

if "work_orders" not in st.session_state:
    st.session_state.work_orders = []

if "fixture_modes" not in st.session_state:
    st.session_state.fixture_modes = {}

if "water_saved" not in st.session_state:
    st.session_state.water_saved = 1248.0

if "cost_saved" not in st.session_state:
    st.session_state.cost_saved = 18.72

if "uptime" not in st.session_state:
    st.session_state.uptime = 99.7


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_fixture(fixture_id):
    """Return fixture metadata by ID."""

    for fixture in FIXTURES:
        if fixture["id"] == fixture_id:
            return fixture

    return None


def get_fixture_mode(fixture_id):
    """Return the active simulation mode for a fixture."""

    return st.session_state.fixture_modes.get(
        fixture_id,
        "NORMAL"
    )


def diagnostic_summary(anomaly):
    """Generate a technician-friendly diagnostic summary."""

    codes = anomaly.get("anomaly_codes", [])

    if "ERR_CONTINUOUS_LEAK" in codes:
        return (
            "Continuous water flow detected with zero occupancy. "
            "Likely micro-leak or faulty valve. Inspect solenoid, "
            "cartridge, and supply connection."
        )

    if "HYGIENE_BREACH" in codes:
        return (
            "Dynamic hygiene index below threshold. "
            "High fixture utilization detected. "
            "Inspect consumables and cleaning schedule."
        )

    if "ERR_ML_ANOMALY" in codes:
        return (
            "Isolation Forest detected an unusual telemetry pattern. "
            "Inspect fixture pressure and water-flow behavior."
        )

    if "ERR_FLOW_ZSCORE" in codes:
        return (
            "Water flow deviates significantly from the rolling "
            "fixture baseline."
        )

    return "No critical fault detected."


def create_work_order(anomaly):
    """Create a technician work order from an anomaly."""

    fixture = get_fixture(anomaly["fixture_id"])

    if fixture is None:
        return

    # Prevent duplicate work orders for the same fixture.
    existing = [
        wo
        for wo in st.session_state.work_orders
        if wo["fixture_id"] == fixture["id"]
    ]

    if existing:
        return

    ticket_id = f"WO-{random.randint(10000, 99999)}"

    work_order = {
        "ticket_id": ticket_id,
        "fixture_id": fixture["id"],
        "fixture_name": fixture["name"],
        "part_number": fixture["part"],
        "summary": diagnostic_summary(anomaly),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    st.session_state.work_orders.append(work_order)


def process_tick(fixture, mode):
    """Generate and analyze one telemetry tick."""

    tick = generate_telemetry_tick(
        zone_id="TERMINAL_A_RESTROOM",
        fixture_id=fixture["id"],
        anomaly_mode=mode,
    )

    result = analyze_tick(tick)

    # Store raw telemetry.
    st.session_state.telemetry.append(tick)

    # Keep only the latest 50 telemetry records.
    st.session_state.telemetry = (
        st.session_state.telemetry[-50:]
    )

    # Store anomalies.
    if result["status"] == "ANOMALY":

        anomaly_record = {
            "timestamp": result["timestamp"],
            "fixture_id": result["fixture_id"],
            "status": result["status"],
            "codes": ", ".join(result["anomaly_codes"]),
            "hygiene_score": result["analytics"]["hygiene_score"],
            "water_flow": result["analytics"]["water_flow_lpm"],
        }

        st.session_state.anomalies.append(
            anomaly_record
        )

        st.session_state.anomalies = (
            st.session_state.anomalies[-30:]
        )

        create_work_order(result)

    return tick, result


def clear_fault(fixture_id):
    """
    Clear the active fault state for a fixture.
    """

    st.session_state.fixture_modes.pop(
        fixture_id,
        None
    )

    st.session_state.work_orders = [
        wo
        for wo in st.session_state.work_orders
        if wo["fixture_id"] != fixture_id
    ]

    # Reset analytics so a previously accumulated leak streak
    # does not immediately re-trigger.
    reset_analytics_state()

    # Re-process the remaining active fixture modes so the
    # dashboard can continue normally.
    st.rerun()


def reset_system():
    """Reset simulation and analytics state."""

    st.session_state.telemetry = []
    st.session_state.anomalies = []
    st.session_state.work_orders = []
    st.session_state.fixture_modes = {}

    st.session_state.water_saved = 1248.0
    st.session_state.cost_saved = 18.72
    st.session_state.uptime = 99.7

    reset_analytics_state()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <h1>💧 AquaSense OS</h1>
        <p style="color:#94a3b8;">
        Kohler Commercial Intelligence Platform
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        "### Simulation Controls",
        unsafe_allow_html=True
    )

    if st.button(
        "🚨 Inject Continuous Leak",
        width='stretch',
    ):

        # Pick a faucet as the faulty fixture.
        leak_fixture = FIXTURES[0]

        st.session_state.fixture_modes[
            leak_fixture["id"]
        ] = "LEAK"

        st.toast(
            f"Leak injected: {leak_fixture['name']}",
            icon="🚨",
        )

        st.rerun()

    if st.button(
        "✈️ Simulate Flight Rush",
        width='stretch',
    ):

        # Put multiple fixtures into high-traffic mode.
        for fixture in FIXTURES:
            st.session_state.fixture_modes[
                fixture["id"]
            ] = "TRAFFIC_SPIKE"

        st.toast(
            "Flight-rush scenario activated.",
            icon="✈️",
        )

        st.rerun()

    if st.button(
        "🔄 Reset System",
        width='stretch',
    ):

        reset_system()

        st.toast(
            "AquaSense system reset.",
            icon="🔄",
        )

        st.rerun()

    st.divider()

    st.markdown(
        """
        **Facility**

        Airport Terminal A

        **Zone**

        Restroom Complex A1

        **Connected Fixtures**

        9

        **System Status**

        🟢 Operational
        """, unsafe_allow_html=True
    )


# ============================================================
# GENERATE LIVE TICKS
# ============================================================

# One telemetry tick per fixture on every Streamlit rerun.
for fixture in FIXTURES:

    mode = get_fixture_mode(
        fixture["id"]
    )

    process_tick(
        fixture,
        mode,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div style="display:flex; justify-content:space-between;
                align-items:center;">

        <div>
            <h1 style="margin-bottom:0;">
                Kohler AquaSense OS
            </h1>

            <p style="color:#94a3b8; font-size:16px;">
                Intelligent Water & Facility Operations Platform
            </p>
        </div>

        <div style="
            background:#1e293b;
            padding:10px 16px;
            border-radius:20px;
            border:1px solid #334155;
            color:#22c55e;
            font-weight:600;
        ">
            ● SYSTEM ONLINE
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PERSONA TABS
# ============================================================

tab_executive, tab_technician = st.tabs(
    [
        "🏢 Executive View",
        "🔧 Field Technician Portal — Marcus",
    ]
)


# ============================================================
# TAB 1 — EXECUTIVE VIEW
# ============================================================

with tab_executive:

    st.markdown(
        "## Facility Head Dashboard"
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">
                    💧 Water Saved
                </div>

                <div class="kpi-value">
                    {st.session_state.water_saved:,.0f} L
                </div>

                <div style="color:#22c55e;">
                    ↑ 12.4% vs baseline
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">
                    💰 Cost Saved
                </div>

                <div class="kpi-value">
                    ${st.session_state.cost_saved:,.2f}
                </div>

                <div style="color:#22c55e;">
                    Estimated operational savings
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">
                    ⚡ System Uptime
                </div>

                <div class="kpi-value">
                    {st.session_state.uptime:.1f}%
                </div>

                <div style="color:#22c55e;">
                    All connected systems operational
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SPATIAL FLOOR PLAN
    # --------------------------------------------------------

    left, right = st.columns(
        [2.2, 1]
    )

    with left:

        st.markdown(
            """
            <div class="dashboard-card">
                <div class="card-header">
                    📍 Live Facility Spatial Map
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig = go.Figure()

        # Background floor-plan zones.
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=16,
            y1=11,
            line=dict(
                color="#475569",
                width=2,
            ),
            fillcolor="#111827",
        )

        # Add fixture markers.
        for fixture in FIXTURES:

            mode = get_fixture_mode(
                fixture["id"]
            )

            # Default status.
            status = "NORMAL"
            marker_color = "#22c55e"

            # Determine status from latest telemetry.
            recent = [
                x
                for x in st.session_state.telemetry
                if x["fixture_id"] == fixture["id"]
            ]

            latest = (
                recent[-1]
                if recent
                else None
            )

            if latest:

                if (
                    latest["occupancy_count_10m"] > 100
                ):
                    status = "HYGIENE WARNING"
                    marker_color = "#f59e0b"

                if (
                    mode == "LEAK"
                    and latest["water_flow_lpm"] > 0.25
                    and latest["occupancy_count_10m"] == 0
                ):
                    status = "ACTIVE LEAK"
                    marker_color = "#ef4444"

            symbol = {
                "Sink": "circle",
                "Urinal": "square",
                "Stall": "diamond",
            }.get(
                fixture["type"],
                "circle",
            )

            fig.add_trace(
                go.Scatter(
                    x=[fixture["x"]],
                    y=[fixture["y"]],
                    mode="markers+text",
                    text=[fixture["name"]],
                    textposition="top center",
                    marker=dict(
                        size=24,
                        color=marker_color,
                        symbol=symbol,
                        line=dict(
                            color="#f8fafc",
                            width=1,
                        ),
                    ),
                    customdata=[[
                        fixture["id"],
                        fixture["type"],
                        status,
                    ]],
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Fixture ID: %{customdata[0]}<br>"
                        "Type: %{customdata[1]}<br>"
                        "Status: %{customdata[2]}"
                        "<extra></extra>"
                    ),
                    name=fixture["type"],
                    showlegend=False,
                )
            )

        # Legend traces.
        for label, color, symbol in [
            ("Normal", "#22c55e", "circle"),
            ("Hygiene Warning", "#f59e0b", "square"),
            ("Active Leak", "#ef4444", "diamond"),
        ]:

            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(
                        size=12,
                        color=color,
                        symbol=symbol,
                    ),
                    name=label,
                )
            )

        # Floor-plan labels.
        fig.add_annotation(
            x=8,
            y=10.3,
            text="<b>SINK / HAND-WASH ZONE</b>",
            showarrow=False,
            font=dict(
                color="#94a3b8",
                size=11,
            ),
        )

        fig.add_annotation(
            x=7,
            y=1,
            text="<b>URINAL ZONE</b>",
            showarrow=False,
            font=dict(
                color="#94a3b8",
                size=11,
            ),
        )

        fig.add_annotation(
            x=14,
            y=10.3,
            text="<b>STALL ZONE</b>",
            showarrow=False,
            font=dict(
                color="#94a3b8",
                size=11,
            ),
        )

        fig.update_layout(
            height=500,
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#111827",
            font=dict(
                color="#e2e8f0"
            ),
            xaxis=dict(
                range=[0, 16],
                showgrid=True,
                gridcolor="#1e293b",
                zeroline=False,
                title="Facility X",
            ),
            yaxis=dict(
                range=[0, 11],
                showgrid=True,
                gridcolor="#1e293b",
                zeroline=False,
                title="Facility Y",
                scaleanchor="x",
                scaleratio=1,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            margin=dict(
                l=20,
                r=20,
                t=45,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )

    # --------------------------------------------------------
    # FACILITY STATUS
    # --------------------------------------------------------

    with right:

        st.markdown(
            """
            <div class="card-header">
                Facility Health
            </div>
            """,
            unsafe_allow_html=True,
        )

        active_leaks = sum(
            1
            for fixture in FIXTURES
            if get_fixture_mode(fixture["id"]) == "LEAK"
        )

        traffic_fixtures = sum(
            1
            for fixture in FIXTURES
            if get_fixture_mode(fixture["id"])
            == "TRAFFIC_SPIKE"
        )

        st.metric(
            "Connected Fixtures",
            len(FIXTURES),
        )

        st.metric(
            "Active Leaks",
            active_leaks,
            delta=(
                "Critical"
                if active_leaks
                else "None detected"
            ),
            delta_color="inverse",
        )

        st.metric(
            "High-Traffic Fixtures",
            traffic_fixtures,
        )

        st.metric(
            "Open Work Orders",
            len(st.session_state.work_orders),
        )

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-header">
                Status Legend
            </div>

            🟢 <b>Normal</b><br>
            Fixture operating within baseline.

            <br>

            🟠 <b>Hygiene Warning</b><br>
            Dynamic hygiene index below threshold.

            <br>

            🔴 <b>Active Leak</b><br>
            Continuous water flow without occupancy.

            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # ANOMALY STREAM
    # --------------------------------------------------------

    st.markdown(
        "## 🚨 Live Anomaly Stream", unsafe_allow_html=True
    )

    if st.session_state.anomalies:

        anomaly_df = pd.DataFrame(
            st.session_state.anomalies
        )

        anomaly_df = anomaly_df.rename(
            columns={
                "timestamp": "Timestamp",
                "fixture_id": "Fixture",
                "status": "Status",
                "codes": "Detection",
                "hygiene_score": "Hygiene Score",
                "water_flow": "Flow (LPM)",
            }
        )

        st.dataframe(
            anomaly_df,
            width='stretch',
            hide_index=True,
        )

    else:

        st.info(
            "No anomalies detected. "
            "System is operating within baseline."
        )


# ============================================================
# TAB 2 — FIELD TECHNICIAN PORTAL
# ============================================================

with tab_technician:

    st.markdown(
        "## 🔧 Marcus — Field Technician Portal", unsafe_allow_html=True
    )

    st.caption(
        "AI-generated work orders prioritized by AquaSense OS."
    )

    # --------------------------------------------------------
    # WORK ORDER SUMMARY
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Open Work Orders",
            len(st.session_state.work_orders),
        )

    with col2:
        critical_count = sum(
            1
            for wo in st.session_state.work_orders
            if "LEAK" in wo["summary"].upper()
        )

        st.metric(
            "Critical",
            critical_count,
        )

    with col3:
        st.metric(
            "Connected Fixtures",
            len(FIXTURES),
        )

    st.divider()

    # --------------------------------------------------------
    # ACTIVE WORK ORDERS
    # --------------------------------------------------------

    st.markdown(
        "### Active Work Orders", unsafe_allow_html=True
    )

    if not st.session_state.work_orders:

        st.success(
            "✓ No active work orders. "
            "All fixtures are currently operational."
        )

    else:

        for work_order in st.session_state.work_orders:

            fixture = get_fixture(
                work_order["fixture_id"]
            )

            st.markdown(
                f"""
                <div class="work-order">

                    <div class="work-order-title">
                        🚨 {work_order["ticket_id"]}
                        &nbsp; — &nbsp;
                        {work_order["fixture_name"]}
                    </div>

                    <br>

                    <div class="work-order-label">
                        Fixture
                    </div>

                    <div class="work-order-value">
                        {work_order["fixture_id"]}
                    </div>

                    <div class="work-order-label">
                        Kohler Part #
                    </div>

                    <div class="work-order-value">
                        {work_order["part_number"]}
                    </div>

                    <div class="work-order-label">
                        LLM Diagnostic Summary
                    </div>

                    <div class="work-order-value">
                        {work_order["summary"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "✓ Acknowledge & Complete",
                key=f"complete_{work_order['ticket_id']}",
                width='content',
            ):

                clear_fault(
                    work_order["fixture_id"]
                )

    # --------------------------------------------------------
    # TECHNICIAN INSTRUCTIONS
    # --------------------------------------------------------

    st.markdown(
        "### 🛠 Recommended Technician Workflow", unsafe_allow_html=True
    )

    workflow_col1, workflow_col2, workflow_col3 = st.columns(3)

    with workflow_col1:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-header">
                01 — Acknowledge
            </div>

            Review the AI diagnostic summary and
            accept the assigned work order.

            </div>
            """,
            unsafe_allow_html=True,
        )

    with workflow_col2:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-header">
                02 — Inspect
            </div>

            Inspect the fixture, valve,
            pressure, and water-flow path.

            </div>
            """,
            unsafe_allow_html=True,
        )

    with workflow_col3:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-header">
                03 — Complete
            </div>

            Resolve the fault and acknowledge
            completion to clear the alert.

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <br>
    <hr style="border-color:#334155;">

    <div style="
        text-align:center;
        color:#64748b;
        font-size:12px;
    ">
        Kohler AquaSense OS · Synthetic IoT Demonstration
        · AI-Assisted Facility Operations
    </div>
    """,
    unsafe_allow_html=True,
)
