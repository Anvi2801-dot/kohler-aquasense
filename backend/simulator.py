"""
Synthetic IoT Telemetry Generator
---------------------------------
Simulates telemetry from Kohler-style commercial fixtures
installed in a high-footfall facility such as an airport terminal restroom.

Supported anomaly modes:
    - NORMAL
    - LEAK
    - TRAFFIC_SPIKE
"""

import random
from datetime import datetime, timezone


def generate_telemetry_tick(zone_id, fixture_id, anomaly_mode=None):
    """
    Generate one synthetic IoT telemetry tick.

    Parameters
    ----------
    zone_id : str
        Identifier for the restroom/facility zone.
    fixture_id : str
        Identifier for the fixture, e.g. KOHLER_FAUCET_101.
    anomaly_mode : str or None
        Supported values:
            NORMAL
            LEAK
            TRAFFIC_SPIKE
        None is treated as NORMAL.

    Returns
    -------
    dict
        A JSON-serializable telemetry object.
    """

    mode = (anomaly_mode or "NORMAL").upper()

    if mode not in {"NORMAL", "LEAK", "TRAFFIC_SPIKE"}:
        raise ValueError(
            "Invalid anomaly_mode. Use NORMAL, LEAK, or TRAFFIC_SPIKE."
        )

    # ---------------------------------------------------------
    # NORMAL MODE
    # ---------------------------------------------------------
    # Water flow is strictly tied to positive occupancy:
    # occupancy = 0  -> flow = 0
    # occupancy > 0  -> flow > 0
    # ---------------------------------------------------------
    if mode == "NORMAL":
        occupancy_count = random.randint(1, 25)

        # More occupants generally imply more water usage.
        # Keep flow within the required 0.0 - 1.5 LPM range.
        water_flow = min(
            1.5,
            round(
                0.15 + (occupancy_count / 25) * random.uniform(0.7, 1.35),
                2
            )
        )

        # Approximate number of flushes during the previous 10 minutes.
        flush_count = min(
            occupancy_count,
            max(0, int(random.gauss(occupancy_count * 0.35, 2)))
        )

        pressure = round(random.uniform(42.0, 58.0), 2)
        diagnostic_code = "OK"

    # ---------------------------------------------------------
    # LEAK MODE
    # ---------------------------------------------------------
    # Fixture continuously consumes water even though there
    # are zero occupants.
    # ---------------------------------------------------------
    elif mode == "LEAK":
        occupancy_count = 0
        water_flow = round(random.uniform(0.6, 1.2), 2)
        flush_count = 0

        # Slightly abnormal but still plausible pressure.
        pressure = round(random.uniform(40.0, 56.0), 2)
        diagnostic_code = "LEAK_DETECTED"

    # ---------------------------------------------------------
    # TRAFFIC SPIKE MODE
    # ---------------------------------------------------------
    # Simulates an unusually high-footfall period such as:
    # boarding rush, event crowd, or terminal peak hour.
    # ---------------------------------------------------------
    else:
        occupancy_count = random.randint(101, 180)

        # High number of flushes during the short observation window.
        flush_count = random.randint(
            max(30, occupancy_count // 3),
            min(occupancy_count, 100)
        )

        # Higher fixture activity, capped at a realistic upper value.
        water_flow = round(
            random.uniform(1.0, 1.5),
            2
        )

        # Increased demand can cause some pressure variation.
        pressure = round(random.uniform(35.0, 52.0), 2)
        diagnostic_code = "TRAFFIC_SPIKE"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zone_id": zone_id,
        "fixture_id": fixture_id,
        "water_flow_lpm": water_flow,
        "flush_count_10m": flush_count,
        "occupancy_count_10m": occupancy_count,
        "pressure_psi": pressure,
        "diagnostic_code": diagnostic_code,
    }


# -------------------------------------------------------------
# TEST BLOCK
# -------------------------------------------------------------
if __name__ == "__main__":

    zone_id = "ZONE_A1"
    fixture_id = "KOHLER_FAUCET_101"

    print("=== Synthetic Kohler IoT Telemetry ===\n")

    # Generate 5 normal telemetry ticks.
    for _ in range(5):
        telemetry = generate_telemetry_tick(
            zone_id,
            fixture_id,
            anomaly_mode="NORMAL"
        )

        print(telemetry)