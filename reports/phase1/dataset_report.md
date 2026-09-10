# TinyIDS V3 — Comprehensive Dataset Inspection Report

**Generated Date**: 2026-09-08  
**Project**: TinyIDS (TinyML-Based Behavioral Intrusion Detection System)  
**Target Hardware**: Arduino Nano ESP32 (ESP32-S3)  
**Author / Lead**: TinyIDS Engineering Team  

---

## 1. Executive Summary

An exhaustive, streaming inspection was conducted on the dataset resources available in the local workspace:
1. **CICIoT2023**: A massive IoT network flow and packet-level dataset comprising **7,845,673 total records** across three pre-partitioned subsets (`train.csv`, `test.csv`, and `validation.csv`), occupying **2.21 GB** on disk.
2. **TON_IoT**: A single connection log file (`ton-iot.csv`) comprising **19 sample records** and **45 attributes** formatted as Zeek (formerly Bro) network connection logs.

This report documents the structural schemas, exact row and feature counts, class distributions, data quality checks (missing values, infinities, zero-variance columns), potential data leakages, and technical feasibility for reproduction on an Arduino Nano ESP32 endpoint.

---

## 2. Dataset Overview & Inventory

| Attribute | CICIoT2023 (`CICIOT23/`) | TON_IoT (`ton-iot.csv`) |
| :--- | :--- | :--- |
| **Location** | `CICIOT23/train/`, `test/`, `validation/` | Workspace root `ton-iot.csv` |
| **Total Files** | 3 CSV files (`train.csv`, `test.csv`, `validation.csv`) | 1 CSV file |
| **Total Size on Disk** | **2,211.88 MB (~2.21 GB)** | **3,317 bytes (3.24 KB)** |
| **Total Rows** | **7,845,673 rows** | **19 rows** (Sample / Preview slice) |
| **Features Count** | **46 predictive features + 1 target (`label`)** | **43 features + `label` + `type`** |
| **Data Format** | Comma-Separated Values (CSV), dense numerical | Comma-Separated Values (CSV), mixed types |
| **Data Granularity** | Flow & packet statistical window aggregates | Individual network connection events (Zeek) |
| **Observation Point**| External Network Tap / Mirror Port (L2–L4) | Network Gateway / Zeek Network Monitor |

---

## 3. CICIoT2023 Detailed Inspection

### 3.1 Partition Breakdown

Streaming chunk-by-chunk verification revealed the following split counts:

- **Train Split (`train.csv`)**: 5,491,971 rows (70.00% of dataset), **1,548.24 MB**
- **Test Split (`test.csv`)**: 1,176,851 rows (15.00% of dataset), **331.84 MB**
- **Validation Split (`validation.csv`)**: 1,176,851 rows (15.00% of dataset), **331.80 MB**
- **Total Rows**: **7,845,673 rows**

### 3.2 Feature Schema & Types

All 46 predictor features in `CICIOT23` are numerical (`float64`). There are no raw string headers in the data rows, and the only categorical column is the target column `label`.

#### Feature Categories in CICIoT2023:
1. **Flow Dynamics & Timing (7 features)**:
   `flow_duration`, `Header_Length`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`
2. **TCP Flags & Handshake Counters (12 features)**:
   `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count`
3. **Protocol Indicators (14 binary flags)**:
   `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC`
4. **Packet Size Statistics (6 features)**:
   `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`
5. **Statistical Distribution & Inter-Arrival (7 features)**:
   `IAT` (Inter-Arrival Time), `Number` (packet count), `Magnitue`, `Radius`, `Covariance`, `Variance`, `Weight`

### 3.3 Data Quality & Anomaly Checks

- **Missing Values (`NaN`, `null`, empty)**: **0 across all 5,491,971 train rows** (0.00%). The dataset is pre-cleaned and fully populated.
- **Infinite Values (`+inf`, `-inf`)**: **0 across all features**.
- **Constant / Zero-Variance Features**:
  - `Telnet`: Min = 0.0, Max = 0.0 (100% zeroes across all 5.49M samples)
  - `IRC`: Min = 0.0, Max = 0.0 (100% zeroes across all 5.49M samples)
  - *Recommendation*: Drop `Telnet` and `IRC` immediately before model training as they carry zero mutual information.
- **Near-Constant Features**:
  - `IPv`: Constant 1.0 for virtually all rows (IPv4 indicator).
  - `LLC`: Constant 1.0 for standard Ethernet/Wi-Fi frame framing.

### 3.4 Label Analysis & Class Distribution (Train Split)

The target column is `label` (string). There are **34 distinct classes** in total, exhibiting extreme class imbalance.

| Class Name | Broad Category | Sample Count (Train) | Percentage |
| :--- | :--- | :---: | :---: |
| **DDoS-ICMP_Flood** | DDoS (Volumetric) | 848,088 | 15.44% |
| **DDoS-UDP_Flood** | DDoS (Volumetric) | 637,558 | 11.61% |
| **DDoS-TCP_Flood** | DDoS (Volumetric) | 528,499 | 9.62% |
| **DDoS-PSHACK_Flood** | DDoS (Volumetric) | 481,254 | 8.76% |
| **DDoS-SYN_Flood** | DDoS (Volumetric) | 478,653 | 8.72% |
| **DDoS-RSTFINFlood** | DDoS (Volumetric) | 475,441 | 8.66% |
| **DDoS-SynonymousIP_Flood** | DDoS (Volumetric) | 422,083 | 7.69% |
| **DoS-UDP_Flood** | DoS (Volumetric) | 390,422 | 7.11% |
| **DoS-TCP_Flood** | DoS (Volumetric) | 314,174 | 5.72% |
| **DoS-SYN_Flood** | DoS (Volumetric) | 237,573 | 4.33% |
| **BenignTraffic** | **Normal / Benign** | **129,538** | **2.36%** |
| **Mirai-greeth_flood** | Mirai Botnet | 116,133 | 2.11% |
| **Mirai-udpplain** | Mirai Botnet | 104,814 | 1.91% |
| **Mirai-greip_flood** | Mirai Botnet | 88,821 | 1.62% |
| **DDoS-ICMP_Fragmentation** | DDoS (Fragment) | 53,046 | 0.97% |
| **MITM-ArpSpoofing** | Spoofing / MITM | 36,316 | 0.66% |
| **DDoS-UDP_Fragmentation** | DDoS (Fragment) | 34,169 | 0.62% |
| **DDoS-ACK_Fragmentation** | DDoS (Fragment) | 33,581 | 0.61% |
| **DNS_Spoofing** | Spoofing / MITM | 21,214 | 0.39% |
| **Recon-HostDiscovery** | Reconnaissance | 15,737 | 0.29% |
| **Recon-OSScan** | Reconnaissance | 11,587 | 0.21% |
| **Recon-PortScan** | Reconnaissance | 9,648 | 0.18% |
| **DoS-HTTP_Flood** | DoS (Application) | 8,487 | 0.15% |
| **VulnerabilityScan** | Reconnaissance | 4,396 | 0.08% |
| **DDoS-HTTP_Flood** | DDoS (Application) | 3,371 | 0.06% |
| **DDoS-SlowLoris** | DoS (Application) | 2,757 | 0.05% |
| **DictionaryBruteForce** | Brute Force | 1,541 | 0.03% |
| **BrowserHijacking** | Web Exploitation | 665 | 0.01% |
| **CommandInjection** | Injection Attack | 620 | 0.01% |
| **SqlInjection** | Injection Attack | 590 | 0.01% |
| **XSS** | Injection Attack | 414 | 0.01% |
| **Backdoor_Malware** | Malware | 392 | 0.01% |
| **Recon-PingSweep** | Reconnaissance | 249 | 0.00% |
| **Uploading_Attack** | Exploitation | 140 | 0.00% |

#### Critical Imbalance Insight:
- **Benign Traffic**: 129,538 samples (**2.36%**)
- **Attack Traffic**: 5,362,433 samples (**97.64%**)
- Volumetric DoS/DDoS attacks account for over 85% of all records.
- Standard accuracy metric is completely misleading here: a naive model that predicts "Attack" on every sample achieves 97.64% accuracy while completely failing to detect legitimate normal behavior!
- Therefore, **Precision, Recall, F1-Score, and False Positive Rate (FPR)** are the mandatory evaluation metrics.

---

## 4. TON_IoT Detailed Inspection

### 4.1 File & Content Structure

The local workspace file `ton-iot.csv` is a **19-record sample snippet** (3.24 KB) representing Zeek network connection logs (`conn.log` extended schema).

- **Total Rows**: 19 records
- **Total Columns**: 45
- **Numeric Features (18)**: `ts`, `src_port`, `dst_port`, `duration`, `src_bytes`, `dst_bytes`, `missed_bytes`, `src_pkts`, `src_ip_bytes`, `dst_pkts`, `dst_ip_bytes`, `dns_qclass`, `dns_qtype`, `dns_rcode`, `http_request_body_len`, `http_response_body_len`, `http_status_code`, `label`
- **Categorical / String Features (27)**: `src_ip`, `dst_ip`, `proto`, `service`, `conn_state`, `dns_query`, `dns_AA`, `dns_RD`, `dns_RA`, `dns_rejected`, `ssl_version`, `ssl_cipher`, `ssl_resumed`, `ssl_established`, `ssl_subject`, `ssl_issuer`, `http_trans_depth`, `http_method`, `http_uri`, `http_version`, `http_user_agent`, `http_orig_mime_types`, `http_resp_mime_types`, `weird_name`, `weird_addl`, `weird_notice`, `type`
- **Missing Value Representation**: Missing or unobserved protocol events are encoded as `'-'` (e.g., in `http_uri`, `ssl_cipher`, `dns_query`).

### 4.2 Labels in the Sample File
- **Binary `label`**: 0 (Normal: 8 samples), 1 (Attack: 11 samples)
- **Subclass `type`**: `ddos` (9 samples), `normal` (8 samples), `dos` (2 samples)

### 4.3 Key Finding Regarding TON_IoT
`ton-iot.csv` in this workspace is an illustrative 19-row schema sample rather than the full multi-GB TON_IoT dataset. Because it only has 19 rows, it **cannot** be used to train statistical machine learning models directly without severe overfitting. However, it serves as an excellent reference for **network connection-level features** (e.g., `duration`, `src_bytes`, `dst_bytes`, `conn_state`, `src_pkts`, `dst_pkts`) which map closely to individual socket transactions on an embedded client.

---

## 5. Potential Data Leakage & Artifact Analysis

1. **Identifier Columns in TON_IoT**:
   - `src_ip` (`192.168.1.31`, `192.168.1.79`, `192.168.1.152`), `dst_ip`, `src_port`.
   - *Risk*: A machine learning model will simply memorize the IP address of the attacker machine (e.g. `192.168.1.31` = attack) rather than learning behavioral patterns. These must be excluded.
2. **Timestamps (`ts`)**:
   - Monotonically increasing Unix epoch timestamps in `ton-iot.csv` (`1554198358` to `1556203822`).
   - *Risk*: Attacks were recorded on specific days; models can split on timestamp ranges rather than traffic dynamics.
3. **Synthetic Flow Generator Artifacts in CICIoT2023**:
   - `Weight`: A parameter used internally by CICFlowMeter's exponential decay weighting.
   - `LLC`, `IPv`, `Telnet`, `IRC`: Zero-variance or near-constant features that must be purged.

---

## 6. Public Features vs. Arduino Nano ESP32 Reality

| Public Dataset Feature | Category | Reproducible on Nano ESP32? | Engineering Rationale |
| :--- | :---: | :---: | :--- |
| **`Rate`, `Srate`, `Drate`** | **B** | **Yes (Derivable)** | Endpoint tracks sent/received packets per second window (`count / dt`). |
| **`Tot sum`, `Tot size`** | **B** | **Yes (Derivable)** | Endpoint sums byte throughput in application layer buffers. |
| **`IAT` (Inter-Arrival Time)**| **B** | **Yes (Derivable)** | Measured between consecutive HTTP/TCP transactions using `micros()`. |
| **`Duration` / `flow_duration`**| **B**| **Yes (Derivable)** | Measured from socket connect to close using hardware timers. |
| **`Protocol Type` (TCP/UDP)** | **A** | **Yes (Direct)** | Known directly by the application firmware architecture. |
| **`HTTP`, `HTTPS`, `DNS`** | **A** | **Yes (Direct)** | Endpoint knows its own application transactions. |
| **TCP Flags (`syn`, `ack`, `fin`)**| **C**| **No (External / Sniffer)** | The Arduino WiFi library encapsulates TCP inside the ESP32 LwIP stack. Extracting raw TCP flags requires promiscuous sniffing or hacking LwIP internals, which drains memory and CPU. |
| **Promiscuous ARP/ICMP sniffer**| **C** | **No (Impractical on MCU)**| An IoT endpoint's CPU should execute device logic, not run Wireshark at 240 MHz. |
| **`Covariance`** | **D** | **No (Too Complex)** | Floating point covariance matrix calculations in the main loop degrade real-time performance. |
| **`free_heap`, `loop_time`** | **A** | **ESP32 Native Only** | **Missing completely from public datasets**, but represents the most critical behavioral telemetry available on the actual microcontroller. |

---

## 7. Next Actions & Experimental Roadmap

1. **Pipeline A (Public Baseline)**:
   - Extract a balanced, clean stratified subset from `CICIOT23/train/train.csv` (e.g., 50,000 to 100,000 samples) to prevent RAM exhaustion while retaining all 34 classes.
   - Evaluate baseline classifiers (Logistic Regression, Decision Tree, Random Forest, Small Neural Network) on the full feature set vs. the **ESP32-compatible subset**.
   - Measure the exact performance drop when transitioning from sniffer-level TCP flags to lightweight rate/timing features.
2. **Pipeline B (Hardware Deployment)**:
   - Build modular firmware on the Arduino Nano ESP32 collecting real network, memory, and timing telemetry (`free_heap`, `heap_delta`, `loop_avg_ms`, `loop_max_ms`, `wifi_rssi`, `packet_rate`, `byte_rate`).
   - Collect normal baseline behavior and controlled anomaly scenarios.
   - Train, quantize (FP32 vs INT8), and deploy the final TinyML model on-device.
