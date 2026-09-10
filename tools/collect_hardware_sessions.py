#!/usr/bin/env python3
"""
TinyIDS — Automated Multi-Session Telemetry Collector for ESP32 Hardware
Connects via USB CDC, switches to CSV mode, cycles through scenarios,
discards transition windows (label 255), and saves structured CSV sessions + metadata.
"""

import os
import sys
import time
import json
import argparse
import serial
import serial.tools.list_ports

EXPECTED_HEADER = "timestamp_ms,window_id,scenario,label,free_heap,min_free_heap,heap_delta,max_alloc_heap,loop_avg_ms,loop_max_ms,loop_jitter_ms,wifi_rssi,tx_count,rx_count,tx_bytes,rx_bytes,transaction_rate,byte_rate,avg_inter_arrival_ms,transaction_count,reconnect_count,socket_errors,socket_duration_ms"
EXPECTED_COL_COUNT = len(EXPECTED_HEADER.split(','))

SCENARIOS = [
    "NORMAL_IDLE",
    "NORMAL_PERIODIC",
    "NORMAL_VARIABLE",
    "ANOMALY_HIGH_RATE",
    "ANOMALY_BURST",
    "ANOMALY_COMPUTE",
    "ANOMALY_MEMORY",
    "ANOMALY_COMBINED"
]

def auto_detect_esp32_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if p.device and "usbmodem" in p.device:
            return p.device
        if p.description and any(kw in p.description.lower() for kw in ["arduino", "esp32", "nano", "nora"]):
            return p.device
    return None

def collect_session(ser, session_id, windows_per_scenario=10, raw_dir="dataset/esp32/raw", meta_dir="dataset/esp32/metadata"):
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)
    
    output_csv = os.path.join(raw_dir, f"{session_id}.csv")
    meta_json = os.path.join(meta_dir, f"{session_id}_metadata.json")
    
    print(f"\n==================================================")
    print(f"  Starting Session Collection: {session_id}")
    print(f"  Target: {len(SCENARIOS)} scenarios x {windows_per_scenario} windows")
    print(f"==================================================")
    
    # Ensure board is in CSV mode
    ser.write(b"CSV\n")
    time.sleep(0.5)
    ser.reset_input_buffer()
    
    valid_rows = 0
    discarded_transitions = 0
    start_time = time.time()
    
    rows_data = []
    
    for sc in SCENARIOS:
        print(f"\n[SCENARIO SWITCH] Sending command: {sc}")
        ser.write(f"{sc}\n".encode('utf-8'))
        time.sleep(0.2)
        
        collected_in_sc = 0
        transition_passed = False
        
        while collected_in_sc < windows_per_scenario:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if not line or "timestamp_ms" in line:
                    continue
                
                parts = line.split(',')
                if len(parts) == EXPECTED_COL_COUNT:
                    lbl = int(parts[3])
                    sc_name = parts[2]
                    
                    if lbl == 255:
                        discarded_transitions += 1
                        print(f"  [TRANSITION DISCARDED] Window {parts[1]} | Scenario: {sc_name}")
                        continue
                    
                    rows_data.append(line)
                    collected_in_sc += 1
                    valid_rows += 1
                    
                    print(f"  [WINDOW {collected_in_sc}/{windows_per_scenario}] Win {parts[1]:>3s} | {sc_name:<20s} | Label: {lbl} | Rate: {parts[16]:>6s} ops/s | LoopAvg: {parts[8]:>6s} ms | Heap: {parts[4]} B", flush=True)
                else:
                    if line:
                        print(f"  [NON-CSV LINE] {line}", flush=True)
            except Exception as e:
                print(f"  [READ ERROR] {e}", flush=True)
                time.sleep(0.2)

    # Write CSV
    with open(output_csv, "w") as f:
        f.write(EXPECTED_HEADER + "\n")
        for r in rows_data:
            f.write(r + "\n")
            
    total_time = round(time.time() - start_time, 2)
    meta_content = {
        "session_id": session_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_windows": valid_rows,
        "discarded_transitions": discarded_transitions,
        "scenarios_collected": SCENARIOS,
        "duration_seconds": total_time,
        "csv_path": output_csv
    }
    with open(meta_json, "w") as f:
        json.dump(meta_content, f, indent=2)
        
    print(f"\n[SUCCESS] Session {session_id} saved to {output_csv}")
    print(f"          Captured {valid_rows} valid telemetry windows in {total_time}s")
    return output_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, default=None)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--sessions", type=int, default=3, help="Number of independent sessions to collect")
    parser.add_argument("--windows", type=int, default=10, help="Windows per scenario per session")
    args = parser.parse_args()

    port = args.port or auto_detect_esp32_port()
    if not port:
        print("[ERROR] No ESP32 serial port found!")
        sys.exit(1)

    print(f"[INFO] Opening serial port {port} at {args.baud} baud...")
    ser = serial.Serial(port, args.baud, timeout=6.0)
    ser.reset_input_buffer()
    time.sleep(1.0)
    
    for i in range(1, args.sessions + 1):
        session_id = f"session_{i:03d}"
        collect_session(ser, session_id, windows_per_scenario=args.windows)
        if i < args.sessions:
            print("\n[COOL DOWN] Pausing 5 seconds between sessions...")
            time.sleep(5.0)

    ser.close()
    print("\n==================================================")
    print("  ALL SESSIONS COLLECTED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
