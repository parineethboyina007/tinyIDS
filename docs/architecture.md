# TinyIDS System Architecture

```text
                               IoT / Network Environment
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │                Arduino Nano ESP32                 │
                 │                 (ESP32-S3 SoC)                    │
                 │                                                   │
                 │  Native USB CDC       WiFi / LwIP     FreeRTOS    │
                 │     Serial              Sockets         Heap      │
                 └─────────┬───────────────────┬─────────────┬───────┘
                           │                   │             │
                           ▼                   ▼             ▼
                 ┌───────────────────────────────────────────────────┐
                 │                 Telemetry Engine                  │
                 │  - Loop Execution Latency (micros(), Welford)     │
                 │  - Memory Dynamics (Free heap, Delta, Min watermark)
                 │  - Traffic Accounting (tx/rx chunks, byte rate)   │
                 │  - RF Health (WiFi.RSSI(), reconnect events)      │
                 │  - Windowing Accumulator (Fixed 5000 ms)          │
                 └─────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │                Feature Preprocessor               │
                 │  Z-score Normalization: x' = (x - mean) / std     │
                 │  (Exact compile-time parity with Python scaler)   │
                 └─────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │                TinyML Inference Engine            │
                 │  - Branch-optimized Decision Tree C++ Model       │
                 │  - Microsecond latency, zero heap allocation      │
                 │  - Binary Classification: NORMAL (0) / ANOMALY (1)│
                 └─────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │          Risk Scoring & Temporal Smoothing        │
                 │  - 3-Window Consensus (2-of-3 majority vote)      │
                 │  - Continuous Behavioral Risk Score (0 - 100)     │
                 │  - Dominant Indicator Attribution                 │
                 └─────────────────────────┬─────────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             [MODE_CSV Data Stream]               [MODE_DASHBOARD Live]
             Machine-readable 5s rows             Human-readable security alerts
             for dataset collection               with confidence & risk metrics
```
