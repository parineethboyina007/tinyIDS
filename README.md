# TinyIDS — TinyML Behavioral Intrusion Detection System for Arduino Nano ESP32

[![Platform](https://img.shields.io/badge/Platform-Arduino%20Nano%20ESP32-blue.svg)](https://docs.arduino.cc/hardware/nano-esp32/)
[![Core](https://img.shields.io/badge/SoC-ESP32--S3%20Xtensa%20LX7-green.svg)](https://www.espressif.com/en/products/socs/esp32-s3)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TinyIDS** is a physically validated, on-device behavioral intrusion detection system (IDS) running locally on the **Arduino Nano ESP32** (ESP32-S3 @ 240 MHz). It features zero-heap TinyML decision tree inference, streaming telemetry extraction, temporal ring-buffer consensus, and an embedded live HTTP security dashboard with SoftAP support.

---

## 1. System Overview

Rather than relying on resource-intensive external network packet sniffers or remote cloud monitors, TinyIDS evaluates **native 10-dimensional endpoint telemetry** right on the microcontroller:

```text
                                  ┌─────────────────────────────┐
                                  │   Laptop / Mobile Client    │
                                  │                             │
                                  │  TinyIDS Web Dashboard UI   │
                                  └──────────────┬──────────────┘
                                                 │
                                           Wi-Fi (SoftAP/STA)
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Arduino Nano ESP32 (ESP32-S3)                         │
│                                                                             │
│  ┌───────────────────────┐          ┌───────────────────────────────────┐   │
│  │ Telemetry Engine      │─────────►│ Feature Vector (10 Dimensions)    │   │
│  │ • Transaction & Bytes │          └─────────────────┬─────────────────┘   │
│  │ • Free Heap & Delta   │                            │                     │
│  │ • Loop Latency & Jitter│                           ▼                     │
│  │ • RSSI & Socket Errors│                 ┌───────────────────┐           │
│  └───────────────────────┘                 │ Z-Score Normaler  │           │
│                                            └──────────┬────────┘           │
│                                                       │                     │
│                                                       ▼                     │
│                                            ┌───────────────────┐           │
│                                            │ TinyML Decision   │           │
│                                            │ Tree (25.7 µs)    │           │
│                                            └──────────┬────────┘           │
│                                                       │                     │
│                                             NORMAL / ANOMALY                │
│                                                       │                     │
│                                                       ▼                     │
│                                            ┌───────────────────┐           │
│                                            │ Risk Meter & 2/3  │           │
│                                            │ Temporal Consensus│           │
│                                            └──────────┬────────┘           │
│                                                       │                     │
│                   ┌───────────────────────────────────┴───────────────┐     │
│                   │                                                   │     │
│             USB CDC Serial                                  WebServer │     │
│             (CSV / Dashboard)                           (GET /api/status)   │
└───────────────────┬───────────────────────────────────────────────────┬─────┘
                    ▼                                                   ▼
            Live Terminal Monitor                             Live Web UI (192.168.4.1)
```

---

## 2. Hardware Telemetry Vector (10 Core Features)

| Feature | Physical Meaning | Measurement Method | Units |
| :--- | :--- | :--- | :---: |
| `transaction_rate` | Application socket read/write operations per second | `(tx_count + rx_count) / window_seconds` | ops/s |
| `byte_rate` | Application payload bytes transferred per second | `(tx_bytes + rx_bytes) / window_seconds` | B/s |
| `free_heap` | Available dynamic memory in internal SRAM | `ESP.getFreeHeap()` | bytes |
| `heap_delta` | Net memory consumption during window | `free_heap_end - free_heap_start` | bytes |
| `loop_avg_ms` | Mean execution duration of `loop()` | Welford streaming algorithm using `micros()` | ms |
| `loop_max_ms` | Worst-case blocking execution duration | Peak loop pass duration across window | ms |
| `loop_jitter_ms` | Standard deviation of loop latency | Numerically stable streaming standard deviation | ms |
| `wifi_rssi` | Wi-Fi Received Signal Strength Indicator | `WiFi.RSSI()` (-127 if offline) | dBm |
| `avg_inter_arrival_ms`| Mean interval between consecutive transactions | Sum of transaction `micros()` deltas / count | ms |
| `socket_errors` | Count of failed connections or socket timeouts | Socket error callback counter | count |

---

## 3. Experimentally Verified Hardware Results

Measured on physical **Arduino Nano ESP32** hardware:

| Metric | Measured Value | Hardware Significance |
| :--- | :---: | :--- |
| **Model Accuracy** | **100.0% (1.0000)** | Evaluated on real ESP32 dataset split |
| **Model Precision** | **100.0% (1.0000)** | Zero false alarms on validation set |
| **Model Recall** | **100.0% (1.0000)** | Zero missed anomalies on validation set |
| **Python / C++ Parity** | **PASS ✓ (10/10 test vectors)** | 100% exact numerical & decision match |
| **Held-Out Anomaly Recall** | **100.0% (9/9 `ANOMALY_COMBINED`)** | Detects unseen fused attack patterns |
| **On-Device Benchmark** | **97.5% (39/40 windows)** | Verified across 8 physical scenarios |
| **Average Inference Latency** | **25.7 microseconds** | Measured directly via `micros()` on ESP32-S3 |
| **Program Flash Storage** | **759,685 bytes (24.1%)** | Leaves 2.38 MB free for application logic |
| **Static SRAM Footprint** | **59,060 bytes (18.0%)** | Leaves 268 KB free for local variables |
| **Runtime Free SRAM** | **~276,664 bytes** | Fully stable heap retention |

---

## 4. On-Device Scenario Detection Matrix

Empirically measured across all 8 physical workload scenarios:

| Scenario | Expected | Captured | Normal | Anomaly | Avg Risk | Max Risk | Avg Latency | Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `NORMAL_IDLE` | NORMAL | 5 | 5 | 0 | 10.0 | 10 | 24.2 µs | **PASS ✓** |
| `NORMAL_PERIODIC` | NORMAL | 5 | 5 | 0 | 6.0 | 10 | 25.0 µs | **PASS ✓** |
| `NORMAL_VARIABLE` | NORMAL | 5 | 5 | 0 | 6.6 | 13 | 25.2 µs | **PASS ✓** |
| `ANOMALY_HIGH_RATE` | ANOMALY | 5 | 1 | 4 | 77.0 | 93 | 25.8 µs | **PASS ✓** |
| `ANOMALY_BURST` | ANOMALY | 5 | 0 | 5 | 85.0 | 85 | 25.4 µs | **PASS ✓** |
| `ANOMALY_COMPUTE` | ANOMALY | 5 | 0 | 5 | 90.6 | 92 | 25.8 µs | **PASS ✓** |
| `ANOMALY_MEMORY` | ANOMALY | 5 | 0 | 5 | 90.6 | 92 | 28.6 µs | **PASS ✓** |
| `ANOMALY_COMBINED` | ANOMALY | 5 | 0 | 5 | 93.0 | 93 | 26.0 µs | **PASS ✓** |

---

## 5. Web Dashboard Demo Procedure

1. **Power Device**: Plug Arduino Nano ESP32 into USB-C.
2. **Connect Wi-Fi**:
   - SSID: `TinyIDS-ESP32`
   - Password: `tinyids123` (configurable in `config_private.h`)
3. **Open Web Browser**:
   - Access: `http://192.168.4.1/` (or Station IP if connected to network)
4. **Live Verification**:
   - Observe live system status banner (**SYSTEM NORMAL** / **⚠️ ANOMALY DETECTED**).
   - View risk meter (0-100), 10-feature telemetry cards, behavioral indicators, decision tree path, and 20-window canvas risk graph.
5. **Scenario Control over Serial**:
   - Open Serial Monitor at 115200 baud.
   - Type commands (`HIGH_RATE`, `COMPUTE`, `BURST`, `MEMORY`, `COMBINED`, `IDLE`, `PERIODIC`) to trigger workloads and observe live dashboard updates.

---

## 6. How to Build & Train

### Prerequisites
- Python 3.9+ with `pyserial`, `scikit-learn`, `pandas`, `numpy`
- Arduino CLI with `arduino:esp32` installed

### Build & Train Pipeline
```bash
# 1. Collect real telemetry from connected ESP32 hardware
python3 tools/collect_hardware_sessions.py --port /dev/cu.usbmodemE8F60ABF87A02 --sessions 2 --windows 5

# 2. Train Decision Tree on hardware telemetry & export C++ code
python3 ml/training/train_and_export.py

# 3. Run C++ / Python parity test
python3 ml/export/parity_test.py

# 4. Compile firmware with Arduino CLI
"/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
  compile --fqbn arduino:esp32:nano_nora firmware/TinyIDS

# 5. Upload firmware to Arduino Nano ESP32
"/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
  upload -p /dev/cu.usbmodemE8F60ABF87A02 --fqbn arduino:esp32:nano_nora firmware/TinyIDS
```

---

## 7. License

Distributed under the MIT License. See `LICENSE` for details.
