#!/usr/bin/env python3
"""
TinyIDS — Physical Hardware Scenario Validation & Performance Benchmarking
Triggers all scenarios on physical ESP32 over serial CDC, captures live on-device predictions,
records measured latency, heap, risk score, and computes scenario accuracy matrix.
"""

import os
import sys
import time
import pandas as pd
import serial
import serial.tools.list_ports

SCENARIOS_TO_TEST = [
    ("NORMAL_IDLE", 0),
    ("NORMAL_PERIODIC", 0),
    ("NORMAL_VARIABLE", 0),
    ("ANOMALY_HIGH_RATE", 1),
    ("ANOMALY_BURST", 1),
    ("ANOMALY_COMPUTE", 1),
    ("ANOMALY_MEMORY", 1),
    ("ANOMALY_COMBINED", 1)
]

def main():
    print("==================================================", flush=True)
    print("  TinyIDS — Physical Hardware Benchmark Suite", flush=True)
    print("==================================================", flush=True)

    port = "/dev/cu.usbmodemE8F60ABF87A02"
    ser = serial.Serial(port, 115200, timeout=6.0)
    ser.reset_input_buffer()
    time.sleep(0.5)

    # Put board in DASHBOARD mode to read structured outputs
    ser.write(b"DASHBOARD\n")
    time.sleep(0.5)

    results = []

    for sc_name, expected_lbl in SCENARIOS_TO_TEST:
        print(f"\n[BENCHMARK] Testing scenario: {sc_name} (Expected: {'ANOMALY' if expected_lbl==1 else 'NORMAL'})", flush=True)
        ser.write(f"{sc_name}\n".encode('utf-8'))
        time.sleep(0.2)

        windows_captured = 0
        normal_cnt = 0
        anomaly_cnt = 0
        fp_cnt = 0
        fn_cnt = 0
        risk_scores = []
        inf_times = []

        while windows_captured < 5:
            line = ser.readline().decode('utf-8', errors='replace').rstrip()
            if not line:
                continue

            if "PREDICTION" in line:
                pred_str = line.split(":")[-1].strip()
                is_anomaly = ("ANOMALY" in pred_str)
                if is_anomaly:
                    anomaly_cnt += 1
                else:
                    normal_cnt += 1

                if expected_lbl == 0 and is_anomaly:
                    fp_cnt += 1
                elif expected_lbl == 1 and not is_anomaly:
                    fn_cnt += 1

            elif "Risk Score" in line:
                # Format: Risk Score : 5 / 100 [LOW]
                try:
                    score_part = line.split(":")[1].split("/")[0].strip()
                    risk_scores.append(int(score_part))
                except:
                    pass

            elif "Inference Time" in line:
                # Format: Inference Time : 24 us
                try:
                    us_part = line.split(":")[1].replace("us", "").strip()
                    inf_times.append(int(us_part))
                    windows_captured += 1
                    print(f"  Captured Window {windows_captured}/5 | Pred: {'ANOMALY' if is_anomaly else 'NORMAL'} | Risk: {risk_scores[-1] if risk_scores else 'N/A'} | Latency: {inf_times[-1]} us", flush=True)
                except:
                    pass

        avg_risk = sum(risk_scores)/len(risk_scores) if risk_scores else 0
        max_risk = max(risk_scores) if risk_scores else 0
        avg_latency = sum(inf_times)/len(inf_times) if inf_times else 0

        results.append({
            "scenario": sc_name,
            "expected_label": expected_lbl,
            "number_of_windows": windows_captured,
            "normal_count": normal_cnt,
            "anomaly_count": anomaly_cnt,
            "false_positives": fp_cnt,
            "false_negatives": fn_cnt,
            "average_risk": round(avg_risk, 1),
            "max_risk": max_risk,
            "avg_inference_us": round(avg_latency, 1)
        })

    ser.close()

    df_res = pd.DataFrame(results)
    out_dir = "reports/final"
    os.makedirs(out_dir, exist_ok=True)
    csv_out = os.path.join(out_dir, "hardware_scenario_results.csv")
    df_res.to_csv(csv_out, index=False)

    print("\n==================================================")
    print("  HARDWARE BENCHMARK COMPLETE!")
    print("==================================================")
    print(df_res.to_string(index=False))
    print(f"\nSaved hardware scenario results to: {csv_out}")

if __name__ == "__main__":
    main()
