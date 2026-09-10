#!/usr/bin/env python3
"""
TinyIDS V3 — Host USB Serial Telemetry Data Collection Tool
Captures machine-readable 5-second window telemetry emitted by Arduino Nano ESP32.
"""

import os
import sys
import time
import argparse
import serial
import serial.tools.list_ports

EXPECTED_HEADER = "timestamp_ms,window_id,scenario,label,free_heap,min_free_heap,heap_delta,max_alloc_heap,loop_avg_ms,loop_max_ms,loop_jitter_ms,wifi_rssi,tx_count,rx_count,tx_bytes,rx_bytes,transaction_rate,byte_rate,avg_inter_arrival_ms,transaction_count,reconnect_count,socket_errors,socket_duration_ms"
EXPECTED_COL_COUNT = len(EXPECTED_HEADER.split(','))

def auto_detect_esp32_port():
    """Detects USB serial port corresponding to Arduino Nano ESP32 or USB CDC."""
    ports = serial.tools.list_ports.comports()
    print("Available serial ports:")
    for p in ports:
        print(f"  - {p.device} | {p.description} | VID:PID={p.vid}:{p.pid}")
        if p.description and any(kw in p.description.lower() for kw in ["arduino", "esp32", "nano", "usbmodem", "usb serial"]):
            return p.device
        if p.device and "usbmodem" in p.device:
            return p.device
    return None

def main():
    parser = argparse.ArgumentParser(description="TinyIDS ESP32 Telemetry Collector")
    parser.add_argument("--port", type=str, default=None, help="Serial port path (auto-detected if omitted)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--duration", type=int, default=300, help="Recording duration in seconds (default: 300s / 5 min)")
    parser.add_argument("--output", type=str, default="dataset/esp32/raw/session_001.csv", help="Output CSV path")
    parser.add_argument("--notes", type=str, default="Smoke test session", help="Session description notes")
    args = parser.parse_args()

    port = args.port
    if not port:
        port = auto_detect_esp32_port()
        if not port:
            print("[ERROR] No Arduino Nano ESP32 detected automatically.")
            print("Please connect the device via USB-C or specify --port manually.")
            sys.exit(1)

    print(f"[INFO] Connecting to {port} at {args.baud} baud...")
    try:
        ser = serial.Serial(port, args.baud, timeout=2.0)
        # Flush buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception as e:
        print(f"[ERROR] Failed to open serial port {port}: {e}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    meta_dir = "dataset/esp32/metadata"
    os.makedirs(meta_dir, exist_ok=True)

    print(f"[INFO] Recording for {args.duration} seconds to {args.output}...")
    
    start_time = time.time()
    valid_rows = 0
    discarded_rows = 0
    header_written = False

    with open(args.output, "w") as f:
        while time.time() - start_time < args.duration:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if not line:
                    continue

                # Check if it is the CSV header
                if "timestamp_ms" in line and "window_id" in line:
                    if not header_written:
                        f.write(line + "\n")
                        f.flush()
                        header_written = True
                        print("[INFO] Captured CSV header.")
                    continue

                # Validate CSV row format
                parts = line.split(',')
                if len(parts) == EXPECTED_COL_COUNT:
                    if not header_written:
                        f.write(EXPECTED_HEADER + "\n")
                        header_written = True
                    f.write(line + "\n")
                    f.flush()
                    valid_rows += 1
                    elapsed = int(time.time() - start_time)
                    print(f"[{elapsed:3d}s] Window {parts[1]:>3s} | Scenario: {parts[2]:<26s} | Label: {parts[3]} | Heap: {parts[4]:>6s} B | Rate: {parts[16]:>6s} ops/s | Loop: {parts[8]:>6s} ms")
                else:
                    discarded_rows += 1
                    print(f"[WARN] Discarded non-CSV line: {line}")
            except KeyboardInterrupt:
                print("\n[INFO] Collection interrupted by user.")
                break
            except Exception as e:
                print(f"[WARN] Read error: {e}")
                time.sleep(0.5)

    ser.close()
    total_elapsed = round(time.time() - start_time, 2)
    print(f"\n=== COLLECTION COMPLETE ===")
    print(f"Total time: {total_elapsed}s")
    print(f"Valid telemetry windows saved: {valid_rows}")
    print(f"Discarded lines: {discarded_rows}")
    print(f"Saved to: {args.output}")

    # Save session metadata
    session_id = os.path.splitext(os.path.basename(args.output))[0]
    meta_path = os.path.join(meta_dir, f"{session_id}_metadata.json")
    meta_content = f"""{{
  "session_id": "{session_id}",
  "date": "{time.strftime('%Y-%m-%d %H:%M:%S')}",
  "duration_seconds": {total_elapsed},
  "valid_windows": {valid_rows},
  "discarded_lines": {discarded_rows},
  "output_file": "{args.output}",
  "port": "{port}",
  "baud": {args.baud},
  "notes": "{args.notes}"
}}"""
    with open(meta_path, "w") as f_meta:
        f_meta.write(meta_content)
    print(f"Metadata saved to: {meta_path}")

if __name__ == "__main__":
    main()
