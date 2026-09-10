# TinyIDS V3 — 5-Minute Live Demonstration Protocol

This protocol allows you to demonstrate TinyIDS live to an evaluator or interviewer in under 5 minutes.

---

### Demonstration Steps

#### 1. Hardware Connection & Setup (1 Minute)
1. Connect the **Arduino Nano ESP32** to your laptop using a USB-C cable.
2. Verify board detection:
   ```bash
   python3 tools/flash_and_test.py
   ```
3. Set operating mode to `MODE_DASHBOARD` in `firmware/TinyIDS/config.h`:
   ```cpp
   #define OPERATING_MODE MODE_DASHBOARD
   ```
4. Flash the firmware:
   ```bash
   "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"        upload -p /dev/cu.usbmodem* --fqbn arduino:esp32:nano_nora firmware/TinyIDS
   ```

#### 2. Normal Baseline Demonstration (2 Minutes)
1. Open the serial terminal at 115200 baud:
   ```bash
   screen /dev/cu.usbmodem* 115200
   ```
2. Observe the live dashboard:
   - **Scenario**: `NORMAL_IDLE` or `NORMAL_PERIODIC`
   - **Transaction Rate**: Low (~1.0 ops/s)
   - **Loop Latency**: Sub-millisecond (~0.2 ms)
   - **Free Heap**: Stable (~268 KB)
   - **Prediction**: `NORMAL`
   - **Risk Score**: `LOW [5 - 15 / 100]`

#### 3. Anomaly Induction & Real-Time Detection (1.5 Minutes)
1. As the scenario controller transitions to `ANOMALY_HIGH_RATE` or `ANOMALY_COMPUTE`:
2. Observe the immediate telemetry shift:
   - **Transaction Rate** surges to 15–20 ops/s
   - **Loop Latency** spikes to 15–25 ms
3. Observe TinyIDS's real-time response:
   - **INFERENCE RESULT**: `!! ANOMALY DETECTED !!`
   - **Confidence**: `98.0%`
   - **Risk Score**: `85 / 100 [CRITICAL]`
   - **Primary Indicator**: `HIGH_TRANSACTION_RATE` or `CPU_LOOP_BLOCKING`
   - **Inference Latency**: `< 50 microseconds`

#### 4. Automatic Recovery (30 Seconds)
1. When the scenario returns to `NORMAL_IDLE`:
2. Observe free heap recovering, rates dropping, and Risk Score returning to `LOW`.
