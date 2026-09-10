# TinyIDS V3 — Feature Semantics & Measurement Definitions

**Version**: 3.0  
**Phase**: 2A (Hardware Telemetry Instrumentation)  
**Target Hardware**: Arduino Nano ESP32 (ESP32-S3)  
**Framework**: Arduino Core v2.0.18-arduino.5 / ESP-IDF v4.4.7  

---

## 1. Terminology & Semantic Grounding (Crucial Distinction)

In external network intrusion detection research (e.g., CICIoT2023), traffic is recorded using promiscuous network taps or mirror ports inspecting raw Layer 2/3 Ethernet frames. On an IoT endpoint running Arduino/ESP-IDF, the application interacts with the **transport/socket layer (Layer 4/7)** via the LwIP TCP/IP stack.

To maintain scientific integrity and prevent invalid claims, TinyIDS strictly adheres to the following definitions:

| Ambiguous Term | TinyIDS Precise Term | Physical Reality on Arduino Nano ESP32 |
| :--- | :--- | :--- |
| **"Packets Sent"** | **`tx_count` (Application Transmit Operations)** | The number of distinct `client.write()` calls executed by the application firmware. |
| **"Packets Received"** | **`rx_count` (Application Receive Operations)** | The number of distinct `client.read()` buffer retrieval operations executed by the firmware. |
| **"Packet Rate"** | **`transaction_rate` (Transactions / Second)** | The total number of application socket read/write operations per unit time: `(tx_count + rx_count) / window_duration_sec`. **NOT Layer 3 IP frames.** |
| **"Flow Duration"** | **`socket_duration_ms`** | Milliseconds elapsed from `client.connect()` until connection termination / socket closure. |
| **"Byte Volume"** | **`tx_bytes` & `rx_bytes`** | Cumulative Layer 7 application payload bytes transferred through socket buffers. Excludes IP/TCP header encapsulation overhead. |

---

## 2. Comprehensive Feature Measurement Specification

Every 5-second aggregation window emits exactly one CSV row containing 23 attributes.

### 2.1 Identifiers & Ground Truth

#### 1. `timestamp_ms`
* **Physical Meaning**: Continuous uptime of the microcontroller since boot.
* **Unit**: Milliseconds (`ms`).
* **Source API**: Arduino `millis()`.
* **Aggregation**: Instantaneous snapshot at window closure.
* **Potential Bias**: Timer rolls over after approximately 49.7 days (handled gracefully by unsigned integer subtraction).

#### 2. `window_id`
* **Physical Meaning**: Monotonically increasing sequence counter of aggregated windows.
* **Unit**: Integer count ($1, 2, 3, \dots$).
* **Aggregation**: Incremented by 1 upon each window finalization.
* **Role**: Primary key ensuring no windows are dropped in serial transit.

#### 3. `scenario`
* **Physical Meaning**: Active operational workload executing on the device.
* **Values**: `NORMAL_IDLE`, `NORMAL_PERIODIC`, `NORMAL_VARIABLE`, `ANOMALY_HIGH_RATE`, `ANOMALY_BURST`, `ANOMALY_CONNECTION_STRESS`, `ANOMALY_COMPUTE`, `ANOMALY_MEMORY`, `ANOMALY_COMBINED`.
* **Role**: Ground truth scenario metadata.

#### 4. `label`
* **Physical Meaning**: Supervised binary security ground truth.
* **Values**:
  - `0`: **NORMAL** (Legitimate operating envelope)
  - `1`: **ANOMALY** (Controlled synthetic stress/abnormal behavior)
  - `255`: **TRANSITION** (Boundary window during workload switch; MUST be purged from training data)

---

### 2.2 Memory Dynamics (Heap Telemetry)

#### 5. `free_heap`
* **Physical Meaning**: Total unallocated dynamic memory available in 8-bit accessible internal SRAM at window closure.
* **Unit**: Bytes (`B`).
* **Source API**: `ESP.getFreeHeap()` / `esp_get_free_heap_size()`.
* **Aggregation**: Instantaneous measurement taken at the exact moment the window closes.
* **Security Relevance**: Detects continuous memory consumption, buffer exhaustion attacks, or memory leaks caused by malicious requests.

#### 6. `min_free_heap`
* **Physical Meaning**: The lowest memory watermark recorded at any point during the 5-second window.
* **Unit**: Bytes (`B`).
* **Source API**: Checked on every `loop()` iteration against `ESP.getFreeHeap()`.
* **Aggregation**: Minimum value across all loop iterations within the window: $\min_{t \in [0, W]} (\text{heap}_t)$.
* **Security Relevance**: Catches temporary heap spikes (e.g., transient buffer allocations) that recover before the window closes and would otherwise be invisible in `free_heap`.

#### 7. `heap_delta`
* **Physical Meaning**: Net change in free memory over the window duration.
* **Unit**: Signed bytes (`int32_t`).
* **Calculation**: $\text{heap\_delta} = \text{free\_heap}_{\text{end}} - \text{free\_heap}_{\text{start}}$.
* **Sign Convention**:
  - **Negative ($-$)**: Memory was consumed/allocated during the window (heap shrank).
  - **Positive ($+$)**: Memory was freed/released during the window (heap expanded).
  - **Zero ($0$)**: Stable memory profile.

#### 8. `max_alloc_heap`
* **Physical Meaning**: Size of the largest single contiguous block of free heap memory.
* **Unit**: Bytes (`B`).
* **Source API**: `ESP.getMaxAllocHeap()` / `heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)`.
* **Aggregation**: Snapshot at window closure.
* **Security Relevance**: Direct indicator of heap fragmentation. If `free_heap` is 80 KB but `max_alloc_heap` is only 4 KB, the heap is heavily fragmented and prone to allocation failures.

---

### 2.3 Execution & Loop Latency Telemetry

#### 9. `loop_avg_ms`
* **Physical Meaning**: Arithmetic mean duration of single `loop()` passes across the window.
* **Unit**: Milliseconds (`ms`).
* **Source API**: Microsecond deltas using `micros()`.
* **Aggregation**: Computed via Welford's streaming algorithm: $\mu = \frac{1}{N} \sum_{i=1}^N \Delta t_i$.
* **Measurement Isolation**: Measured strictly across application workload logic; serial CSV printing time is **excluded** to prevent observation bias.

#### 10. `loop_max_ms`
* **Physical Meaning**: Longest single loop pass recorded during the window.
* **Unit**: Milliseconds (`ms`).
* **Aggregation**: $\max_{i \in [1, N]} (\Delta t_i)$.
* **Security Relevance**: Detects blocking socket I/O, network lockups, and CPU starvation caused by compute or flood stress.

#### 11. `loop_jitter_ms`
* **Physical Meaning**: Standard deviation (variability) of loop execution times across the window.
* **Unit**: Milliseconds (`ms`).
* **Aggregation**: Numerically stable streaming standard deviation: $\sigma = \sqrt{\frac{M_2}{N - 1}}$.
* **Security Relevance**: Steady normal operation displays minimal jitter; erratic bursts and computational attacks cause high jitter.

---

### 2.4 Wireless / RF Telemetry

#### 12. `wifi_rssi`
* **Physical Meaning**: Received Signal Strength Indicator of the Wi-Fi link.
* **Unit**: Decibel-milliwatts (`dBm`), typically $-30\text{ dBm}$ (strong) to $-90\text{ dBm}$ (weak).
* **Source API**: `WiFi.RSSI()`. Returns $-100\text{ dBm}$ if disconnected.
* **Aggregation**: Instantaneous reading at window closure.
* **Security Context**: Contextual feature. RSSI alone does NOT signify an attack, but distinguishes environmental signal degradation from software-induced latency.

#### 13. `reconnect_count`
* **Physical Meaning**: Number of Wi-Fi disconnection / reconnection cycles triggered in the window.
* **Unit**: Event count.
* **Security Relevance**: Detects Wi-Fi deauthentication attacks, beacon jamming, or AP dropouts.

---

### 2.5 Application-Level Traffic & Volume Telemetry

#### 14. `tx_count`
* **Physical Meaning**: Number of application socket write operations in the window.
* **Unit**: Operations count.
* **Aggregation**: Incremented on every `client.write()` call.

#### 15. `rx_count`
* **Physical Meaning**: Number of application socket read operations in the window.
* **Unit**: Operations count.
* **Aggregation**: Incremented on every `client.read()` call with available payload.

#### 16. `tx_bytes`
* **Physical Meaning**: Total application payload bytes transmitted in the window.
* **Unit**: Bytes (`B`).

#### 17. `rx_bytes`
* **Physical Meaning**: Total application payload bytes received in the window.
* **Unit**: Bytes (`B`).

#### 18. `transaction_rate`
* **Physical Meaning**: Frequency of application transfer operations per second.
* **Unit**: Transactions / second ($\text{ops/s}$).
* **Calculation**: $\text{transaction\_rate} = \frac{\text{tx\_count} + \text{rx\_count}}{\text{window\_duration\_s}}$.

#### 19. `byte_rate`
* **Physical Meaning**: Total application throughput per second.
* **Unit**: Bytes / second ($\text{B/s}$).
* **Calculation**: $\text{byte\_rate} = \frac{\text{tx\_bytes} + \text{rx\_bytes}}{\text{window\_duration\_s}}$.

#### 20. `avg_inter_arrival_ms`
* **Physical Meaning**: Average elapsed time between consecutive socket transaction events.
* **Unit**: Milliseconds (`ms`).
* **Aggregation**: Sum of microsecond transaction deltas divided by event count.

#### 21. `transaction_count`
* **Physical Meaning**: Total socket operations in the window: `tx_count + rx_count`.
* **Unit**: Integer count.

#### 22. `socket_errors`
* **Physical Meaning**: Count of failed socket connection attempts or write timeouts.
* **Unit**: Event count.

#### 23. `socket_duration_ms`
* **Physical Meaning**: Mean elapsed time from socket connection to teardown.
* **Unit**: Milliseconds (`ms`).

---

## 3. Equivalence Mapping: CICIoT2023 vs. TinyIDS

| CICIoT2023 Public Feature | TinyIDS Endpoint Feature | Semantic Equivalence | Mapping Confidence |
| :--- | :--- | :--- | :---: |
| `Rate` (Total packets/s) | `transaction_rate` (Ops/s) | **Functional Proxy**: Measures operational velocity; public metric counts raw IP frames, TinyIDS counts application transactions. | **HIGH** |
| `Tot size` / `Tot sum` | `tx_bytes + rx_bytes` | **Direct Equivalence**: Measures byte payload volume transferred. | **HIGH** |
| `IAT` (Inter-Arrival Time) | `avg_inter_arrival_ms` | **Direct Equivalence**: Measures interval between consecutive network transactions. | **HIGH** |
| `flow_duration` / `Duration` | `socket_duration_ms` | **Direct Equivalence**: Measures lifetime of active network connection. | **HIGH** |
| `rst_count` / `syn_count` | `socket_errors` | **Behavioral Proxy**: Connection resets and rejected SYNs surface on endpoint as socket connection errors. | **MEDIUM** |
| `urg_count`, `psh_flag` | *None* | Hidden inside ESP32 LwIP stack; cannot be observed without raw sniffer. | **NOT MAPPABLE** |
| *None (Missing in CIC)* | `free_heap`, `heap_delta` | Native hardware memory telemetry unique to TinyIDS endpoint. | **NATIVE ONLY** |
| *None (Missing in CIC)* | `loop_avg_ms`, `loop_jitter_ms`| Native microcontroller CPU execution health unique to TinyIDS endpoint. | **NATIVE ONLY** |
| *None (Missing in CIC)* | `wifi_rssi` | Native RF link quality unique to TinyIDS endpoint. | **NATIVE ONLY** |
