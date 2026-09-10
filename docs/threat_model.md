# TinyIDS Threat Model & Security Scope

## 1. Protected Asset & Assumptions
* **Protected System**: IoT endpoint running on an Arduino Nano ESP32 (ESP32-S3).
* **Network Environment**: Local 802.11 b/g/n Wi-Fi network.
* **Adversary Model**:
  - Remote network-adjacent attacker capable of sending bursts of socket requests.
  - Remote attacker performing volumetric connection stress (DoS / flood attempts).
  - Malicious workload triggering CPU computation exhaustion or memory allocation pressure.

## 2. In-Scope Anomalies
1. **Volumetric Transaction Flooding (`ANOMALY_HIGH_RATE`)**: High frequency socket transactions saturating device bandwidth.
2. **Traffic Bursting (`ANOMALY_BURST`)**: Intermittent packet bursts attempting to cause queue backpressure.
3. **Connection Exhaustion (`ANOMALY_CONNECTION_STRESS`)**: Rapid socket connect/disconnect cycles attempting to exhaust LwIP sockets.
4. **Computational Starvation (`ANOMALY_COMPUTE`)**: Workloads monopolizing the single/dual-core CPU and causing loop latency spikes.
5. **Memory Pressure / Allocation Spikes (`ANOMALY_MEMORY`)**: Transient heap consumption targeting device out-of-memory crashes.

## 3. Out-of-Scope Threats
1. Physical tampering / JTAG probing / side-channel attacks on the ESP32 silicon.
2. Passive eavesdropping on encrypted traffic without behavioral disruption.
3. Exploits against third-party machines that do not route through or target the endpoint.
