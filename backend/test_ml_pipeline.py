import time
from sklearn.ensemble import IsolationForest
import numpy as np

# --- Pipeline Implementation ---
_ml_model = IsolationForest(
    n_estimators=100,
    contamination=0.10,
    random_state=42
)
_is_model_trained = False

def train_baseline_model():
    global _ml_model, _is_model_trained
    np.random.seed(42)
    # 200 samples of clean, normal operational baseline
    clean_baseline_data = np.random.normal(
        loc=[0.5, 3, 15, 2.2],   # [flow, flushes, occupancy, pressure]
        scale=[0.1, 1, 3, 0.1],
        size=(200, 4)
    )
    _ml_model.fit(clean_baseline_data)
    _is_model_trained = True

def detect_ml_anomaly(fixture_id, features):
    global _ml_model, _is_model_trained
    if not _is_model_trained:
        train_baseline_model()
    
    # Pure inference
    prediction = _ml_model.predict([features])[0]
    return prediction == -1


# --- Test Suite ---
def run_tests():
    print("🧪 Running ML Pipeline Tests...\n")

    # TEST 1: Normal Operational Flow
    normal_vector = [0.52, 3, 14, 2.18]
    is_anomaly = detect_ml_anomaly("PNQ_T2_01", normal_vector)
    print(f"Test 1 [Normal Reading]: Vector {normal_vector}")
    print(f"Result: {'🚨 Anomaly' if is_anomaly else '✅ Normal'} (Expected: ✅ Normal)")
    assert not is_anomaly, "Failed: Normal baseline flagged as anomaly!"

    # TEST 2: High Flow / Zero Occupancy Leak
    leak_vector = [4.8, 0, 0, 1.2] # High water flow, no flushes, zero occupancy, low pressure
    is_anomaly = detect_ml_anomaly("PNQ_T2_01", leak_vector)
    print(f"\nTest 2 [Severe Leak]: Vector {leak_vector}")
    print(f"Result: {'🚨 Anomaly' if is_anomaly else '✅ Normal'} (Expected: 🚨 Anomaly)")
    assert is_anomaly, "Failed: Severe leak missed!"

    # TEST 3: Data Poisoning Immunity (Simulate 20 consecutive leak ticks)
    print("\nTest 3 [Data Poisoning Stress Test]: Streaming 20 consecutive leak ticks...")
    poison_failures = 0
    for tick in range(1, 21):
        flag = detect_ml_anomaly("PNQ_T2_01", leak_vector)
        if not flag:
            poison_failures += 1
            print(f"  ❌ Tick {tick}: Model got poisoned! Flagged leak as Normal.")

    if poison_failures == 0:
        print("  ✅ PASS: All 20 continuous leak ticks were successfully detected as Anomalies!")
        print("     (Model baseline remained uncorrupted).")

    # TEST 4: Benchmark Latency
    print("\nTest 4 [Inference Latency Benchmark]:")
    start_time = time.perf_counter()
    for _ in range(100):
        detect_ml_anomaly("PNQ_T2_01", normal_vector)
    end_time = time.perf_counter()
    avg_latency_ms = ((end_time - start_time) / 100) * 1000
    print(f"  ⚡ Average Latency per Tick: {avg_latency_ms:.4f} ms")

if __name__ == "__main__":
    run_tests()