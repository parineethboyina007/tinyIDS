# TinyIDS V3 — Phase 2A: Modular Firmware Architecture & Validation Report

**Verification Date**: 2026-09-08  
**Phase**: 2A (Firmware Implementation & Structural Verification)  
**Target Hardware**: Arduino Nano ESP32 (`arduino:esp32:nano_nora`)  
**Core Version**: `arduino:esp32` v2.0.18-arduino.5  
**Compilation Status**: **SUCCESS (Exit code 0)**  

---

## 1. Hardware & Toolchain Specifications

* **Microcontroller**: Espressif ESP32-S3 (Xtensa dual-core 32-bit LX7 @ 240 MHz).
* **Storage / Flash Partition**: 16 MB QSPI Flash (app partition allocated to 3,145,728 bytes).
* **Internal SRAM**: 512 KB SRAM (~327,680 bytes user data space).
* **USB Interface**: Native USB CDC (USB-OTG peripheral).
* **Compilation Command**:
  ```bash
  "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
      compile --fqbn arduino:esp32:nano_nora firmware/TinyIDS
  ```

---

## 2. Firmware Architecture & Module Separation

The firmware is organized into strictly decoupled modules under `firmware/TinyIDS/`:

```text
firmware/TinyIDS/
├── TinyIDS.ino                 # Setup, main loop, module orchestration
├── config.h                    # Build constants, safety limits, scenario definitions
├── config_private.example.h    # Gitignored Wi-Fi credential template
├── telemetry.h / .cpp          # Welford streaming loop stats, window accumulator
├── traffic_generator.h / .cpp  # Safe onboard synthetic workloads & stress generators
├── scenario_manager.h / .cpp   # Scenario state controller, transition discard policy
└── serial_logger.h / .cpp      # Clean, non-blocking CSV serializer
```

---

## 3. Telemetry Structure & Actual Memory Size

### Struct Memory Footprint Verification
A compile-time `static_assert` was placed directly inside `TinyIDS.ino`:
```cpp
static_assert(sizeof(TelemetryWindow) == 76,
              "TelemetryWindow struct size must be exactly 76 bytes.");
```
* **Hypothesized Size in Previous Proposal**: ~68 bytes.
* **Actual Compiled Size on 32-bit Xtensa**: **76 bytes**.
* **Reason for Difference**:
  1. Inclusion of diagnostic `max_alloc_heap` (4 bytes) to monitor heap fragmentation.
  2. Natural 4-byte struct word alignment boundaries enforced by the GCC Xtensa compiler.

At **76 bytes per window**, storing an in-memory ring buffer of 20 historical windows requires only **1,520 bytes (1.5 KB)**, which is less than 0.6% of the ESP32-S3's available RAM.

---

## 4. Hardware Resource Benchmarks

| Metric | API-Verification Sketch | Complete Phase 2A Firmware | Delta / Overhead | Available Capacity | Usage Percentage |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Program Storage (Flash)** | 704,397 bytes | **707,525 bytes** | +3,128 bytes | 3,145,728 bytes | **22.49%** |
| **Global Dynamic Memory (SRAM)**| 56,616 bytes | **56,444 bytes** | -172 bytes | 327,680 bytes | **17.22%** |
| **Free Dynamic SRAM** | 271,064 bytes | **271,236 bytes** | +172 bytes | — | **82.78% Free** |

*Takeaway*: The entire modular telemetry engine, traffic generator, scenario manager, and serial CSV logger adds only **3.1 KB of flash** and zero dynamic heap degradation, leaving **271.2 KB of free SRAM** available for TinyML models.

---

## 5. Precise Feature Semantics & Terminology

To preserve scientific rigor:
1. **Application Socket Transactions vs. IP Packets**:
   Arduino's `WiFiClient` communicates via high-level socket streams. TinyIDS explicitly measures `tx_count` and `rx_count` as **application-level socket read/write operations**, NOT Layer 3 IP frames.
2. **`transaction_rate`**:
   Computed as `(tx_count + rx_count) / window_duration_sec` (operations per second).
3. **Loop Isolation**:
   `loop_avg_ms`, `loop_max_ms`, and `loop_jitter_ms` are measured around application workload execution using `micros()`. Serial CSV printing time is strictly excluded so host baud rate does not bias the telemetry.
4. **Transition Policy**:
   Whenever the scenario switches, the first window is tagged with `label = 255` (`LABEL_TRANSITION`) so mixed boundary behavior is never used for machine learning training.

---

## 6. Safety Limits Implemented

The firmware enforces hard microcontroller guards to prevent bricking or watchdog resets:
* `MIN_SAFE_FREE_HEAP = 40960` (40 KB): Memory stress aborts immediately if heap drops below 40 KB.
* `MAX_COMPUTE_CHUNK_MS = 25`: CPU stress executes in bounded 25 ms chunks, yielding to FreeRTOS to feed the watchdog timer.
* `MAX_CONNS_PER_WINDOW = 60`: Sockets are capped per window to prevent local network disruption.
* `MAX_STRESS_ALLOC_BYTES = 49152` (48 KB): Absolute ceiling on temporary dynamic allocations.

---

## 7. Flashing & Smoke-Test Instructions

When the Arduino Nano ESP32 is connected via USB-C to the computer:

### Step 1: Detect Board Port
```bash
python3 tools/collect_esp32_data.py --help
```
Or list ports:
```bash
"/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" board list
```

### Step 2: Flash the Firmware
```bash
"/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
    upload -p /dev/cu.usbmodemXXXX --fqbn arduino:esp32:nano_nora firmware/TinyIDS
```

### Step 3: Run 5-Minute Smoke Test
```bash
python3 tools/collect_esp32_data.py \
    --port /dev/cu.usbmodemXXXX \
    --duration 300 \
    --output dataset/esp32/raw/smoke_test_001.csv
```
