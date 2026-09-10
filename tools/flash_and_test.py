#!/usr/bin/env python3
"""
TinyIDS V3 — One-Command Board Detection, Upload & Smoke-Test Tool
Automates detecting the Nano ESP32 port, compiling, flashing, and launching the test.
"""

import os
import sys
import time
import subprocess
import serial.tools.list_ports

ARDUINO_CLI = "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
FQBN = "arduino:esp32:nano_nora"
SKETCH = "firmware/TinyIDS"

def detect_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        dev = p.device
        if "usbmodem" in dev or "arduino" in desc or "esp32" in desc or "nora" in desc:
            return dev
    return None

def main():
    print("=== TinyIDS Arduino Nano ESP32 Automation Tool ===")
    port = detect_port()
    if not port:
        print("[STATUS] Arduino Nano ESP32 is NOT currently detected on USB serial.")
        print("[ACTION REQUIRED] Please connect your Arduino Nano ESP32 to the Mac using USB-C.")
        sys.exit(1)

    print(f"[INFO] Detected Arduino Nano ESP32 on port: {port}")
    
    # 1. Compile
    print("[1/3] Compiling firmware...")
    comp = subprocess.run([ARDUINO_CLI, "compile", "--fqbn", FQBN, SKETCH], capture_output=True, text=True)
    if comp.returncode != 0:
        print("[ERROR] Compilation failed:\n", comp.stderr)
        sys.exit(1)
    print("      Compilation successful!")

    # 2. Upload
    print(f"[2/3] Flashing firmware to {port}...")
    up = subprocess.run([ARDUINO_CLI, "upload", "-p", port, "--fqbn", FQBN, SKETCH], capture_output=True, text=True)
    if up.returncode != 0:
        print("[ERROR] Upload failed:\n", up.stderr)
        sys.exit(1)
    print("      Upload completed successfully!")

    # 3. Launch Smoke Test Collector
    print("[3/3] Starting 5-minute automated telemetry smoke test...")
    os.system(f"python3 tools/collect_esp32_data.py --port {port} --duration 300 --output dataset/esp32/raw/smoke_test_001.csv")

if __name__ == "__main__":
    main()
