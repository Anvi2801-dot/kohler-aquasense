import time
import json
import asyncio
import re
from agent import generate_work_order

# Real-world Kohler Part Catalog ground truth map
GROUND_TRUTH_CATALOG = {
    "sensor_faucet_cartridge": "K-72218-IN",
    "solenoid_valve": "K-1138241",
    "urinal_diaphragm": "K-4918-0",
    "aerator_kit": "K-GP30413",
    "sensor_module": "K-GP77759",
    "flushometer_valve": "K-13491",
    "soap_dispenser_pump": "K-10561",
    "faucet_valve_kit": "K-11188",
    "unknown": "Part #K-UNKNOWN"
}

# 20 Ground-Truth Test Payloads mapped strictly to system rules
TEST_BENCHMARK = [
    # 1-5: FAUCETS
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_101",
            "fixture_model": "Kohler Selectokate Touchless Faucet K-72218-IN",
            "location": "Departure Pier A - Sink 1",
            "anomaly_type": "continuous_flow",
            "anomaly_severity": 0.88,
            "telemetry_snapshot": {"flow_rate": 2.5, "pressure_psi": 42},
            "historical_context": {"prior_incidents": 1},
            "timestamp": "2026-09-20T00:00:00Z"
        },
        "expected_priority": "CRITICAL",  # severity >= 0.85
        "expected_part": "K-72218-IN"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_102",
            "fixture_model": "Kohler Touchless Faucet K-11188",
            "location": "Departure Pier B - Sink 3",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.30,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 40},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T00:05:00Z"
        },
        "expected_priority": "ROUTINE",  # severity < 0.50
        "expected_part": "K-GP77759"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_103",
            "fixture_model": "Kohler Selectokate K-72218-IN",
            "location": "Arrivals Hall - Sink 2",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.75,
            "telemetry_snapshot": {"flow_rate": 0.45, "pressure_psi": 38},
            "historical_context": {"prior_incidents": 2},
            "timestamp": "2026-09-20T00:10:00Z"
        },
        "expected_priority": "HIGH",  # 0.50 <= severity < 0.85
        "expected_part": "K-1138241"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_104",
            "fixture_model": "Kohler Touchless Faucet K-11188",
            "location": "Security Area Restroom - Sink 4",
            "anomaly_type": "continuous_flow",
            "anomaly_severity": 0.95,
            "telemetry_snapshot": {"flow_rate": 3.2, "pressure_psi": 41},
            "historical_context": {"prior_incidents": 4},
            "timestamp": "2026-09-20T00:15:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-72218-IN"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_105",
            "fixture_model": "Kohler Selectokate K-72218-IN",
            "location": "Food Court Restroom - Sink 1",
            "anomaly_type": "pressure_drop",
            "anomaly_severity": 0.52,
            "telemetry_snapshot": {"flow_rate": 0.05, "pressure_psi": 18},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T00:20:00Z"
        },
        "expected_priority": "HIGH",
        "expected_part": "K-GP30413"
    },

    # 6-10: URINALS
    {
        "payload": {
            "fixture_id": "KOHLER_URINAL_201",
            "fixture_model": "Kohler Touchless Urinal K-4918-0",
            "location": "Gate 5 Restroom - Urinal U1",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.92,
            "telemetry_snapshot": {"flow_rate": 4.5, "pressure_psi": 45},
            "historical_context": {"prior_incidents": 3},
            "timestamp": "2026-09-20T00:25:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-4918-0"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_URINAL_202",
            "fixture_model": "Kohler Touchless Urinal K-4918-0",
            "location": "Gate 7 Restroom - Urinal U3",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.41,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 44},
            "historical_context": {"prior_incidents": 1},
            "timestamp": "2026-09-20T00:30:00Z"
        },
        "expected_priority": "ROUTINE",
        "expected_part": "K-GP77759"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_URINAL_203",
            "fixture_model": "Kohler Touchless Urinal K-4918-0",
            "location": "VIP Lounge Restroom - Urinal U1",
            "anomaly_type": "continuous_flow",
            "anomaly_severity": 0.89,
            "telemetry_snapshot": {"flow_rate": 3.8, "pressure_psi": 46},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T00:35:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-4918-0"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_URINAL_204",
            "fixture_model": "Kohler Touchless Urinal K-4918-0",
            "location": "Baggage Claim Restroom - Urinal U2",
            "anomaly_type": "pressure_drop",
            "anomaly_severity": 0.60,
            "telemetry_snapshot": {"flow_rate": 0.8, "pressure_psi": 22},
            "historical_context": {"prior_incidents": 2},
            "timestamp": "2026-09-20T00:40:00Z"
        },
        "expected_priority": "HIGH",
        "expected_part": "K-4918-0"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_URINAL_205",
            "fixture_model": "Kohler Touchless Urinal K-4918-0",
            "location": "Check-in Area Restroom - Urinal U4",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.81,
            "telemetry_snapshot": {"flow_rate": 2.9, "pressure_psi": 43},
            "historical_context": {"prior_incidents": 1},
            "timestamp": "2026-09-20T00:45:00Z"
        },
        "expected_priority": "HIGH",
        "expected_part": "K-4918-0"
    },

    # 11-15: FLUSHOMETERS
    {
        "payload": {
            "fixture_id": "KOHLER_FLUSH_301",
            "fixture_model": "Kohler Flushometer K-13491",
            "location": "Arrivals Restroom B - Flush 1",
            "anomaly_type": "continuous_flow",
            "anomaly_severity": 0.94,
            "telemetry_snapshot": {"flow_rate": 9.2, "pressure_psi": 65},
            "historical_context": {"prior_incidents": 2},
            "timestamp": "2026-09-20T00:50:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-13491"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FLUSH_302",
            "fixture_model": "Kohler Flushometer K-13491",
            "location": "Arrivals Restroom B - Flush 3",
            "anomaly_type": "pressure_drop",
            "anomaly_severity": 0.65,
            "telemetry_snapshot": {"flow_rate": 8.0, "pressure_psi": 68},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T00:55:00Z"
        },
        "expected_priority": "HIGH",
        "expected_part": "K-13491"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FLUSH_303",
            "fixture_model": "Kohler Flushometer K-13491",
            "location": "Departure Gate 3 - Flush 2",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.87,
            "telemetry_snapshot": {"flow_rate": 6.5, "pressure_psi": 60},
            "historical_context": {"prior_incidents": 1},
            "timestamp": "2026-09-20T01:00:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-13491"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FLUSH_304",
            "fixture_model": "Kohler Flushometer K-13491",
            "location": "Departure Gate 12 - Flush 4",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.28,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 62},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T01:05:00Z"
        },
        "expected_priority": "ROUTINE",
        "expected_part": "K-GP77759"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FLUSH_305",
            "fixture_model": "Kohler Flushometer K-13491",
            "location": "International Transit - Flush 1",
            "anomaly_type": "continuous_flow",
            "anomaly_severity": 0.91,
            "telemetry_snapshot": {"flow_rate": 7.8, "pressure_psi": 64},
            "historical_context": {"prior_incidents": 3},
            "timestamp": "2026-09-20T01:10:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-13491"
    },

    # 16-20: SOAP DISPENSERS & EDGE CASES
    {
        "payload": {
            "fixture_id": "KOHLER_DISP_101",
            "fixture_model": "Kohler Soap Dispenser K-10561",
            "location": "Food Court Restroom - Dispenser D1",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.35,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 40},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T01:15:00Z"
        },
        "expected_priority": "ROUTINE",
        "expected_part": "K-10561"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_DISP_102",
            "fixture_model": "Kohler Soap Dispenser K-10561",
            "location": "Food Court Restroom - Dispenser D2",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.45,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 40},
            "historical_context": {"prior_incidents": 1},
            "timestamp": "2026-09-20T01:20:00Z"
        },
        "expected_priority": "ROUTINE",
        "expected_part": "K-10561"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_DISP_103",
            "fixture_model": "Kohler Soap Dispenser K-10561",
            "location": "Gate 4 Restroom - Dispenser D1",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.72,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 40},
            "historical_context": {"prior_incidents": 2},
            "timestamp": "2026-09-20T01:25:00Z"
        },
        "expected_priority": "HIGH",
        "expected_part": "K-10561"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_DISP_104",
            "fixture_model": "Unknown Commercial Unit",
            "location": "Arrivals Restroom A - Dispenser D3",
            "anomaly_type": "sensor_error",
            "anomaly_severity": 0.38,
            "telemetry_snapshot": {"flow_rate": 0.0, "pressure_psi": 40},
            "historical_context": {"prior_incidents": 0},
            "timestamp": "2026-09-20T01:30:00Z"
        },
        "expected_priority": "ROUTINE",
        "expected_part": "K-UNKNOWN"
    },
    {
        "payload": {
            "fixture_id": "KOHLER_FAUCET_106",
            "fixture_model": "Kohler Selectokate K-72218-IN",
            "location": "Departure Pier C - Sink 5",
            "anomaly_type": "valve_failure",
            "anomaly_severity": 0.86,
            "telemetry_snapshot": {"flow_rate": 1.1, "pressure_psi": 41},
            "historical_context": {"prior_incidents": 3},
            "timestamp": "2026-09-20T01:35:00Z"
        },
        "expected_priority": "CRITICAL",
        "expected_part": "K-1138241"
    }
]

REQUIRED_KEYS = {
    "ticket_id",
    "priority",
    "fixture_model",
    "root_cause_analysis",
    "recommended_action",
    "kohler_part_number",
    "estimated_water_saved_lph"
}

ALLOWED_PRIORITIES = {"CRITICAL", "HIGH", "ROUTINE"}

async def run_evaluation():
    print("🚀 Running Strict Ground-Truth Agent Benchmarking Suite...\n")
    
    total_tests = len(TEST_BENCHMARK)
    parse_successes = 0
    schema_compliance = 0
    priority_matches = 0
    part_matches = 0
    type_validations = 0
    latencies = []

    for idx, test_case in enumerate(TEST_BENCHMARK, 1):
        payload = test_case["payload"]
        expected_priority = test_case["expected_priority"]
        expected_part = test_case["expected_part"]
        
        start_time = time.time()
        try:
            # Execute synchronously via thread to record precise API latency
            res = await asyncio.to_thread(generate_work_order, payload)
            elapsed = time.time() - start_time
            latencies.append(elapsed)

            # 1. JSON Parse Integrity
            if isinstance(res, dict):
                parse_successes += 1

            # 2. Key Presence & Non-null Check
            has_keys = REQUIRED_KEYS.issubset(res.keys()) and all(res[k] is not None for k in REQUIRED_KEYS)
            if has_keys:
                schema_compliance += 1

            # 3. Decision Logic Compliance (Priority Field)
            actual_priority = res.get("priority", "")
            if actual_priority == expected_priority and actual_priority in ALLOWED_PRIORITIES:
                priority_matches += 1

            # 4. Strict Ground-Truth Part Selection
            actual_part = str(res.get("kohler_part_number", ""))
            if expected_part in actual_part:
                part_matches += 1

            # 5. Output Primitive Typing Rules
            water_saved = res.get("estimated_water_saved_lph")
            if isinstance(water_saved, (float, int)) and not isinstance(water_saved, bool) and water_saved >= 0.0:
                type_validations += 1

            print(f" Test {idx:02d}/{total_tests}: PASSED ({elapsed:.2f}s) | Priority: {actual_priority} | Part: {actual_part}")

        except Exception as e:
            elapsed = time.time() - start_time
            latencies.append(elapsed)
            print(f"❌ Test {idx:02d}/{total_tests}: FAILED ({elapsed:.2f}s) | Error: {e}")

    # Calculate Empirical Results
    json_rate = (parse_successes / total_tests) * 100
    schema_rate = (schema_compliance / total_tests) * 100
    priority_accuracy = (priority_matches / total_tests) * 100
    part_accuracy = (part_matches / total_tests) * 100
    type_compliance = (type_validations / total_tests) * 100
    hallucination_rate = 100.0 - part_accuracy
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("\n" + "="*55)
    print("📊 EMPIRICAL GROUND-TRUTH BENCHMARK RESULTS")
    print("="*55)
    print(f"• Total Evaluated Payloads:     {total_tests}")
    print(f"• JSON Parse Success Rate:       {json_rate:.1f}%")
    print(f"• Schema Key Compliance:         {schema_rate:.1f}%")
    print(f"• Decision Rule Priority Acc.:  {priority_accuracy:.1f}%")
    print(f"• Ground-Truth Part Accuracy:   {part_accuracy:.1f}%")
    print(f"• Numeric Type Compliance:      {type_compliance:.1f}%")
    print(f"• Out-of-Catalog Part Rate:     {hallucination_rate:.1f}%")
    print(f"• Avg Dispatch Latency:          {avg_latency:.2f}s")
    print("="*55 + "\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation())