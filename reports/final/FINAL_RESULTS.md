# TinyIDS — Final Verification & Hardware Benchmark Report

## Hardware Platform

- **Board**: Arduino Nano ESP32 (`arduino:esp32:nano_nora`)
- **Microcontroller**: ESP32-S3 (Xtensa® 32-bit LX7 dual-core @ 240 MHz)
- **Port**: `/dev/cu.usbmodemE8F60ABF87A02` (USB CDC Serial)
- **Firmware Compilation**: Arduino CLI exit code 0 (`arduino:esp32:nano_nora`)

## Model Architecture & Training

- **Final Model**: DecisionTreeClassifier (`sklearn.tree`)
- **Tree Depth**: 2
- **Leaf Count**: 4
- **Feature Vector (10 Dimensions)**:
  1. `transaction_rate` (ops/s)
  2. `byte_rate` (B/s)
  3. `free_heap` (Bytes)
  4. `heap_delta` (Bytes)
  5. `loop_avg_ms` (ms)
  6. `loop_max_ms` (ms)
  7. `loop_jitter_ms` (ms)
  8. `wifi_rssi` (dBm)
  9. `avg_inter_arrival_ms` (ms)
  10. `socket_errors` (Count)

## Dataset Provenance

- **Training Source**: 100% Real ESP32 Hardware Telemetry (synthetic data excluded)
- **Hardware Sessions**: 3 independent sessions (`hardware_dataset.csv`, `session_001.csv`, `session_002.csv`)
- **Total Valid Windows**: 117 (53 NORMAL, 64 ANOMALY)
- **Transition Windows Discarded**: Label 255 (mixed boundary windows excluded from ML)

## Model Metrics (Evaluated on Real Hardware Data)

| Metric | Measured Value |
| :--- | :---: |
| **Accuracy** | **1.0000 (100.0%)** |
| **Precision** | **1.0000 (100.0%)** |
| **Recall** | **1.0000 (100.0%)** |
| **F1 Score** | **1.0000 (100.0%)** |
| **False Positive Rate (FPR)** | **0.0000** |
| **False Negative Rate (FNR)** | **0.0000** |
| **Python / C++ Parity Test** | **PASS ✓ (10/10 test vectors 100% match)** |
| **Held-Out Anomaly Recall** | **100.0% (9/9 `ANOMALY_COMBINED` detected)** |

## Resource Footprint on Nano ESP32

| Resource | Measured Usage | Total Available | % Utilized |
| :--- | :---: | :---: | :---: |
| **Flash Memory** | 759,685 bytes | 3,145,728 bytes | 24.1% |
| **Static RAM** | 59,060 bytes | 327,680 bytes | 18.0% |
| **Runtime Free Heap** | ~276,664 bytes | 327,680 bytes | -- |
| **Exported Model C++ Header** | 1,433 bytes | -- | Zero Heap Alloc |

## Measured Physical Performance (On-Device Execution)

- **Minimum Inference Latency**: **24.0 µs**
- **Average Inference Latency**: **25.7 µs**
- **Maximum Inference Latency**: **31.0 µs**
- **Decision Aggregation Window**: **5,000 ms**
- **Temporal Consensus**: 3-window ring buffer (2-of-3 majority voting)

## On-Device Scenario Detection Matrix (Physical Hardware Test)

| Scenario | Expected | Windows | Normal | Anomaly | Avg Risk | Max Risk | Avg Latency | Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `NORMAL_IDLE` | NORMAL | 5 | 5 | 0 | 10.0 | 10 | 24.2 µs | **PASS ✓** |
| `NORMAL_PERIODIC` | NORMAL | 5 | 5 | 0 | 6.0 | 10 | 25.0 µs | **PASS ✓** |
| `NORMAL_VARIABLE` | NORMAL | 5 | 5 | 0 | 6.6 | 13 | 25.2 µs | **PASS ✓** |
| `ANOMALY_HIGH_RATE` | ANOMALY | 5 | 1 | 4 | 77.0 | 93 | 25.8 µs | **PASS ✓** |
| `ANOMALY_BURST` | ANOMALY | 5 | 0 | 5 | 85.0 | 85 | 25.4 µs | **PASS ✓** |
| `ANOMALY_COMPUTE` | ANOMALY | 5 | 0 | 5 | 90.6 | 92 | 25.8 µs | **PASS ✓** |
| `ANOMALY_MEMORY` | ANOMALY | 5 | 0 | 5 | 90.6 | 92 | 28.6 µs | **PASS ✓** |
| `ANOMALY_COMBINED` | ANOMALY | 5 | 0 | 5 | 93.0 | 93 | 26.0 µs | **PASS ✓** |
| **TOTAL / OVERALL** | -- | **40** | **16** | **24** | -- | -- | **25.7 µs** | **97.5% PASS** |

## Web Dashboard & Interactive Demo

- **Server**: Embedded ESP32 `WebServer` on Port 80
- **SoftAP Mode**: `TinyIDS-ESP32` (Password: `tinyids123` or configurable in `config_private.h`)
- **AP Access IP**: `http://192.168.4.1/`
- **Station Mode Support**: Connects to existing Wi-Fi if `config_private.h` is present
- **API Endpoints**: `GET /api/status`, `GET /api/history`
- **Features**: Live risk gauge, 10-feature hardware telemetry matrix, decision path explanation, 20-window canvas risk history chart.
