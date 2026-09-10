# TinyIDS V3 — Phase 1: Public Dataset Baseline Research Report

**Experiment Date**: 2026-09-08  
**Experiment ID**: `EXP-PHASE1-BASELINE-V3`  
**Random Seed**: 42 (Fully Deterministic)  
**Author**: TinyIDS Engineering Team (Embedded, TinyML, Cybersecurity)  
**Target Hardware Context**: Arduino Nano ESP32 (ESP32-S3, 512 KB SRAM, 16 MB Flash)  

---

## 1. Research Question & Objective

The primary objective of Phase 1 is to answer the central research question:

> **How much detection performance is lost or retained when transitioning from a full 44-feature network sniffer feature space toward a lightweight 14-feature space that can realistically be measured by an Arduino Nano ESP32 endpoint?**

This is an empirical research baseline to establish whether endpoint-observable network features (rates, byte totals, inter-arrival times, payload statistics) retain sufficient predictive power to distinguish normal traffic from malicious anomalies before deploying to physical hardware.

---

## 2. Dataset & Sampling Methodology

### 2.1 Dataset Inventory
- **Dataset**: Canadian Institute for Cybersecurity IoT Dataset 2023 (`CICIoT2023`).
- **Raw Volume**: 7,845,673 total records (2.21 GB) partitioned across `train.csv` (5,491,971 rows), `validation.csv` (1,176,851 rows), and `test.csv` (1,176,851 rows).
- **Class Composition**: 34 distinct classes (1 Benign class, 33 Attack classes).
- **Raw Class Imbalance**: Benign traffic represents only **2.36%** of raw training data, while volumetric floods represent **97.64%**.

### 2.2 Streaming Sampling Strategy
To avoid memory exhaustion and eliminate the "accuracy paradox" (where predicting all attacks yields 97.64% accuracy):
1. **Split Preservation**: Samples were drawn exclusively from their respective official files without cross-partition shuffling or leakage.
2. **Balanced Binary Formulation**: A 1:1 ratio (50% NORMAL vs. 50% ANOMALY) was enforced in every split.
3. **Stratified Attack Representation**: Attack samples were allocated across all 33 attack classes with a minimum quota to preserve rare attacks (e.g., `Uploading_Attack`, `SqlInjection`, `Backdoor_Malware`).
4. **Volume**:
   - **Training Set**: 70,000 samples (35,000 Normal, 35,000 Anomaly)
   - **Validation Set**: 15,000 samples (7,500 Normal, 7,500 Anomaly)
   - **Test Set**: 15,000 samples (7,500 Normal, 7,500 Anomaly)
   - **Total**: 100,000 samples (~37 MB in RAM).

---

## 3. Preprocessing & Feature Set Definition

### 3.1 Preprocessing Pipeline
- **Z-Score Normalization**: Features were standardized using:
  $$\tilde{x} = \frac{x - \mu}{\sigma}$$
  where mean ($\mu$) and standard deviation ($\sigma$) were fitted **strictly on the training split** and applied to validation and test splits.
- **Zero-Variance Purge**: `Telnet` and `IRC` were permanently removed (100% constant zero across all records).

### 3.2 Feature Set Taxonomy

```text
               ┌─────────────────────────────────────────────────────────┐
               │                SET A — FULL_PUBLIC (44)                 │
               │  All valid non-constant features in CICIoT2023          │
               └──────────────────────────┬──────────────────────────────┘
                                          │ (Remove sniffer artifacts, L2 framing)
                                          ▼
               ┌─────────────────────────────────────────────────────────┐
               │           SET B — NETWORK_OBSERVABLE (25)               │
               │  Gateway/Sniffer flow stats, TCP flags, transport protos │
               └──────────────────────────┬──────────────────────────────┘
                                          │ (Remove sniffer-only TCP flags & headers)
                                          ▼
               ┌─────────────────────────────────────────────────────────┐
               │             SET C — ESP32_ENDPOINT (14)                 │
               │  Purely endpoint-measurable rates, bytes, timing, sizes  │
               └─────────────────────────────────────────────────────────┘
```

1. **`SET A — FULL_PUBLIC` (44 features)**:
   The complete non-constant feature space: flow duration, packet rates, TCP flags/counts (`syn`, `ack`, `fin`, `rst`, `urg`, `ece`, `cwr`), protocol indicators, packet size moments (`Min`, `Max`, `AVG`, `Std`, `Tot sum`, `Tot size`), and statistical dispersion (`IAT`, `Number`, `Magnitue`, `Radius`, `Covariance`, `Variance`, `Weight`).
2. **`SET B — NETWORK_OBSERVABLE` (25 features)**:
   A realistic gateway/switch IDS feature set: `flow_duration`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`, `syn_flag_number`, `rst_flag_number`, `ack_flag_number`, `ack_count`, `syn_count`, `fin_count`, `rst_count`, `TCP`, `UDP`, `ICMP`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Variance`.
3. **`SET C — ESP32_ENDPOINT` (14 features)**:
   The subset an Arduino Nano ESP32 can realistically generate using native socket/application telemetry without promiscuous sniffing:
   `flow_duration`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`.

---

## 4. Empirical Evaluation Results

All four candidate models were trained on the 70,000-sample training set and evaluated on the untouched 15,000-sample test set across all three feature sets.

### 4.1 Master Model Comparison Table

| Feature Set | Model | Accuracy | Precision | Recall | F1-Score | FPR | FNR | Parameters | Serialized Size | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SET A (Full 44)** | Logistic Regression | 0.9787 | 0.9921 | 0.9651 | 0.9784 | 0.77% | 3.49% | 45 weights | 1.04 KB | < 0.001 ms |
| **SET A (Full 44)** | **Decision Tree** | **0.9929** | **0.9989** | **0.9869** | **0.9929** | **0.11%** | **1.31%** | **93 nodes** | **8.38 KB** | **< 0.001 ms** |
| **SET A (Full 44)** | Random Forest | 0.9909 | 1.0000 | 0.9817 | 0.9908 | 0.00% | 1.83% | 16,960 nodes | 1,341.51 KB | 0.0015 ms |
| **SET A (Full 44)** | Small NN (MLP) | 0.9891 | 0.9996 | 0.9785 | 0.9889 | 0.04% | 2.15% | 1,985 weights | 54.33 KB | < 0.001 ms |
| **SET B (Net Obs 25)**| Logistic Regression | 0.9767 | 0.9908 | 0.9623 | 0.9763 | 0.89% | 3.77% | 26 weights | 0.88 KB | < 0.001 ms |
| **SET B (Net Obs 25)**| **Decision Tree** | **0.9899** | **0.9990** | **0.9807** | **0.9898** | **0.09%** | **1.93%** | **91 nodes** | **8.23 KB** | **< 0.001 ms** |
| **SET B (Net Obs 25)**| Random Forest | 0.9917 | 0.9997 | 0.9837 | 0.9917 | 0.03% | 1.63% | 15,314 nodes | 1,212.89 KB | 0.0009 ms |
| **SET B (Net Obs 25)**| Small NN (MLP) | 0.9877 | 0.9977 | 0.9776 | 0.9875 | 0.23% | 2.24% | 1,377 weights | 40.19 KB | < 0.001 ms |
| **SET C (ESP32 14)** | Logistic Regression | 0.9245 | 0.8972 | 0.9589 | 0.9270 | 10.99% | 4.11% | 15 weights | 0.80 KB | < 0.001 ms |
| **SET C (ESP32 14)** | **Decision Tree** | **0.9920** | **0.9985** | **0.9855** | **0.9919** | **0.15%** | **1.45%** | **117 nodes** | **10.26 KB** | **< 0.001 ms** |
| **SET C (ESP32 14)** | Random Forest | 0.9927 | 0.9999 | 0.9856 | 0.9927 | 0.01% | 1.44% | 18,766 nodes | 1,482.63 KB | 0.0009 ms |
| **SET C (ESP32 14)** | Small NN (MLP) | 0.9861 | 0.9999 | 0.9723 | 0.9859 | 0.01% | 2.77% | 1,025 weights | 31.44 KB | < 0.001 ms |

---

## 5. Critical Technical Insights

### 5.1 The Decision Tree Discovery
The most significant finding of Phase 1 is that the **Decision Tree retains 99.19% F1-score with only 0.15% False Positive Rate on the 14 ESP32-endpoint features**.
- On `SET A` (44 features): F1 = 0.9929
- On `SET C` (14 features): F1 = 0.9919
- **Performance Drop**: Only **-0.10% F1-score**!
- Furthermore, the Decision Tree model has only **117 nodes**, requiring **10.26 KB** uncompressed, which translates to nested `if/else` statements executing in microseconds on an ESP32 with zero floating-point matrix dependencies.

### 5.2 Failure of Linear Models on Reduced Features
While Logistic Regression performed respectably on the 44-feature set (F1 = 0.9784, FPR = 0.77%), its performance degraded significantly on `SET C`:
- FPR increased to **10.99%** (824 false alarms out of 7,500 normal samples).
- Precision dropped from 99.21% to 89.72%.
- *Root Cause*: Intrusions and normal traffic cannot be separated linearly using rate and size features alone; nonlinear thresholds (e.g. `Rate > X AND Tot_size < Y`) are mandatory.

### 5.3 Random Forest Overhead vs. Benefit
Random Forest achieved 0.9927 F1 on `SET C`, which is virtually identical to the single Decision Tree (0.9919 F1, difference of 0.08%). However:
- Random Forest requires **18,766 nodes across 50 trees**, taking **1,482 KB (~1.48 MB)**.
- Deploying a 1.5 MB model onto an ESP32 with 512 KB SRAM is inefficient and wasteful. A compact Decision Tree or a quantized Neural Network is dramatically superior for TinyML.

---

## 6. Feature Importance & Progressive Reduction

### 6.1 Top Contributing Features (from `feature_importance.csv`)
1. `rst_count` (22.95% RF Gini importance): High in public dataset due to testbed TCP connection resets during flood attacks.
2. `urg_count` (14.99%): Anomalous TCP flag in testbed.
3. `Variance` (11.00%): Packet size variance across the flow window.
4. `Tot size` (6.64%): Cumulative byte volume (Mappable to ESP32: **HIGH**).
5. `AVG` (6.63%): Mean transaction payload size (Mappable to ESP32: **HIGH**).
6. `Std` (4.52%): Standard deviation of payload sizes (Mappable to ESP32: **HIGH**).
7. `flow_duration` (3.63%): Connection lifetime (Mappable to ESP32: **HIGH**).
8. `Min` (3.10%): Minimum payload chunk size (Mappable to ESP32: **HIGH**).
9. `IAT` (1.66%): Inter-arrival time between transactions (Mappable to ESP32: **HIGH**).

### 6.2 Progressive Feature Reduction Curve

| Feature Count ($k$) | Top Retained Features | Decision Tree F1 | Decision Tree FPR | Random Forest F1 | Random Forest FPR |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **44 (Full)** | `rst_count, urg_count, Variance, Tot size, AVG...` | 0.9930 | 0.09% | 0.9910 | 0.00% |
| **25** | `rst_count, urg_count, Variance, Tot size, AVG...` | 0.9926 | 0.20% | 0.9931 | 0.00% |
| **15** | `rst_count, urg_count, Variance, Tot size, AVG...` | 0.9936 | 0.08% | 0.9905 | 0.01% |
| **10** | `rst_count, urg_count, Variance, Tot size, AVG...` | 0.9846 | 0.32% | 0.9845 | 0.11% |
| **8** | `rst_count, urg_count, Variance, Tot size, AVG...` | 0.9836 | 0.27% | 0.9829 | 0.11% |
| **5** | `rst_count, urg_count, Variance, Tot size, AVG` | 0.9841 | 0.24% | 0.9845 | 0.12% |

*Key Finding*: Even when reduced to just **5 core features**, detection F1-score remains above **98.4%**, demonstrating that high-dimensional sniffer captures are largely redundant for volumetric anomaly detection.

---

## 7. Multiclass Research Experiment Findings

When trained on the 14 ESP32-endpoint features to classify into 9 distinct categories:
- **Macro Average F1**: **0.6989 (Decision Tree)**, **0.6062 (Random Forest)**.
- **High-Volume Attacks**:
  - `BENIGN`: Precision = 98.55%, Recall = 99.89%, F1 = **0.9922**
  - `DDoS`: Precision = 99.55%, Recall = 99.85%, F1 = **0.9970**
  - `DoS`: Precision = 99.62%, Recall = 98.88%, F1 = **0.9925**
  - `Mirai`: Precision = 99.54%, Recall = 99.31%, F1 = **0.9942**
- **Stealth / Low-Volume Attacks**:
  - `BruteForce` (10 samples): F1 = **0.0000** (0% detection)
  - `Web_Exploit` (50 samples): F1 = **0.5000** (Recall = 34.00%)
  - `Spoofing` (81 samples): F1 = **0.5645** (Recall = 43.21%)
  - `Reconnaissance` (71 samples): F1 = **0.6780** (Recall = 56.34%)

*Conclusion*: Low-rate, stealthy exploits (like brute force or command injection) do not distort macroscopic network flow statistics. On an embedded endpoint, network flow telemetry alone cannot differentiate attack subtypes; however, **Binary Anomaly Detection** succeeds with >99% F1-score.

---

## 8. Artifacts & Generated Figures

1. **Top Feature Importance Plot**:  
   `reports/figures/feature_importance.png`  
   *Visualizes the 15 most informative features, distinguishing ESP32-compatible vs. sniffer-only attributes.*
2. **Feature Set Comparison**:  
   `reports/figures/feature_set_comparison.png`  
   *Displays test F1-scores across all 4 models and 3 feature sets.*
3. **Feature Reduction Curve**:  
   `reports/figures/feature_count_vs_f1.png`  
   *Tracks detection performance and FPR trade-offs from 44 down to 5 features.*
4. **Endpoint Confusion Matrices**:  
   `reports/figures/confusion_matrices.png`  
   *Depicts True Positives, True Negatives, False Positives, and False Negatives for the 4 models evaluated on `SET C`.*

---

## 9. Limitations of the Public Dataset Baseline

1. **External Observer Bias**:
   CICIoT2023 was captured on network taps, not on microcontrollers. It contains zero hardware state metrics.
2. **Missing Endpoint Telemetry**:
   Free heap memory, heap fragmentation, execution loop latency, CPU cycle jitter, and Wi-Fi RSSI—the most sensitive indicators of local device stress—are completely absent in CICIoT2023.
3. **Domain Shift**:
   A model trained exclusively on CICIoT2023 network flows will suffer domain shift if deployed directly to an ESP32 because synthetic packet generators do not capture the timing jitter and memory dynamics of ESP-IDF FreeRTOS tasks.

---

## 10. Phase 1 Engineering Recommendation

Based on the empirical evidence gathered across 100,000 samples and 12 model evaluations, our recommendation for the feature set to serve as the foundation for the actual ESP32 hardware dataset is:

### **Recommendation: OPTION D — MODIFIED ESP32 ENDPOINT FEATURE SET**

#### Why Option D?
- **Option A (Full Public)** is physically impossible without promiscuous sniffing hardware.
- **Option B (Network Observable)** requires TCP flag counters that are hidden inside the ESP32 LwIP stack.
- **Option C (Pure Public ESP32 Features)** proved that 14 network features achieve **99.19% F1-score** on volumetric attacks, but failed completely on stealthy attacks (0% F1 on brute force, 50% on web exploits).
- **Option D (Modified Endpoint Set)**: We take the best performing network dynamics from Option C (`packet_rate`, `byte_rate`, `tot_bytes`, `inter_arrival_ms`, `socket_duration`) and **fuse them with Native ESP32 System Telemetry**:
  1. `free_heap` & `heap_delta` (detects memory exhaustion and buffer buildup during exploits)
  2. `loop_avg_ms` & `loop_max_ms` (detects CPU blocking, thread starvation, and computational exhaustion)
  3. `wifi_rssi` & `reconnect_cnt` (detects wireless deauthentication, jamming, and RF instability).

This hybrid feature set bridges the gap between public network research and physical embedded reality.
