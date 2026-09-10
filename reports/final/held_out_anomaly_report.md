# TinyIDS — Held-Out Behavioral Anomaly Evaluation Report

**Held-Out Scenario**: `ANOMALY_COMBINED` (Fused High-Rate Traffic + CPU Compute Stress)  
**Training Scenarios**: `NORMAL_IDLE`, `NORMAL_PERIODIC`, `NORMAL_VARIABLE`, `ANOMALY_HIGH_RATE`, `ANOMALY_BURST`, `ANOMALY_COMPUTE`, `ANOMALY_MEMORY`  

| Metric | Measured Value | Security Significance |
| :--- | :---: | :--- |
| **Held-Out Detection Recall** | **100.00%** | Demonstrates the Decision Tree learns generalized multi-feature behavioral boundaries rather than memorizing specific scenario signatures. |
| **Total Held-Out Samples** | 9 | Real ESP32 telemetry windows |
| **Successfully Flagged** | 9 | Predicted as ANOMALY (label 1) |
| **False Negatives** | 0 | Missed windows |
