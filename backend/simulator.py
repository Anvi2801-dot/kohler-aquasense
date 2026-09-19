"""
Synthetic IoT Telemetry Generator
---------------------------------
Simulates telemetry from Kohler-style commercial fixtures
installed in a high-footfall facility such as an airport terminal restroom.

Supported anomaly modes:
    - NORMAL
    - LEAK
    - HYGIENE_WARNING
    - TRAFFIC_SPIKE
"""

import random
from datetime import datetime, timezone


def generate_telemetry_tick(zone_id, fixture_id, anomaly_mode=None):
    """
    Generate one synthetic IoT telemetry tick.
    """

    mode = (anomaly_mode or "NORMAL").upper()

    if mode not in {"NORMAL", "LEAK", "HYGIENE_WARNING", "TRAFFIC_SPIKE"}:
        raise ValueError(
            "Invalid anomaly_mode. Use NORMAL, LEAK, HYGIENE_WARNING, or TRAFFIC_SPIKE."
        )

    # ---------------------------------------------------------
    # NORMAL MODE
    # ---------------------------------------------------------
    if mode == "NORMAL":
        occupancy_count = random.randint(1, 25)
        water_flow = min(
            1.5,
            round(
                0.15 + (occupancy_count / 25) * random.uniform(0.7, 1.35),
                2
            )
        )
        flush_count = min(
            occupancy_count,
            max(0, int(random.gauss(occupancy_count * 0.35, 2)))
        )
        pressure = round(random.uniform(42.0, 58.0), 2)
        diagnostic_code = "OK"

    # ---------------------------------------------------------
    # LEAK MODE
    # ---------------------------------------------------------
    elif mode == "LEAK":
        occupancy_count = 0
        water_flow = round(random.uniform(0.95, 1.05), 2)  # Centered around 1.0 LPM (~60 L/hr)
        flush_count = 0
        pressure = round(random.uniform(40.0, 56.0), 2)
        diagnostic_code = "LEAK_DETECTED"

    # ---------------------------------------------------------
    # HYGIENE WARNING MODE
    # ---------------------------------------------------------
    elif mode == "HYGIENE_WARNING":
        occupancy_count = random.randint(15, 40)
        water_flow = 0.0  # Stagnation / lack of flushing
        flush_count = 0
        pressure = round(random.uniform(45.0, 55.0), 2)
        diagnostic_code = "STAGNATION_RISK"

    # ---------------------------------------------------------
    # TRAFFIC SPIKE MODE (Dynamic realistic variation)
    # ---------------------------------------------------------
    else:
        # High footfall (160-220) with 0 flushes forces hygiene score < 30 (Hygiene Breach)
        occupancy_count = random.randint(160, 220)
        flush_count = 0        
        water_flow = round(random.uniform(0.95, 1.45), 2)
        pressure = round(random.uniform(41.0, 53.0), 2)
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


if __name__ == "__main__":
    zone_id = "PNQ_NITB_DEPARTURE_ZONE_3"
    fixture_id = "KOHLER_FAUCET_101"

    print("Synthetic Kohler IoT Telemetry (PNQ NITB Test)\n")
    for _ in range(5):
        telemetry = generate_telemetry_tick(
            zone_id,
            fixture_id,
            anomaly_mode="TRAFFIC_SPIKE"
        )
        print(telemetry)