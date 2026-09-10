# TinyIDS V3 — Unseen Behavioral Anomaly Experiment Report

**Held-Out Scenario**: `ANOMALY_COMBINED` (Fused High-Rate + Compute Stress)  
**Training Scenarios**: `NORMAL_IDLE`, `NORMAL_PERIODIC`, `NORMAL_VARIABLE`, `ANOMALY_HIGH_RATE`, `ANOMALY_BURST`, `ANOMALY_CONNECTION_STRESS`, `ANOMALY_COMPUTE`, `ANOMALY_MEMORY`  
**Evaluation**: Tested strictly on unseen `ANOMALY_COMBINED` windows  

| Metric | Measured Value | Security Significance |
| :--- | :---: | :--- |
| **Unseen Detection Recall** | **100.00%** | Demonstrates the model learns general anomalous boundaries rather than memorizing individual attack profiles. |
| **Total Unseen Test Samples** | 66 | Held-out behavioral windows |
| **Successfully Detected** | 66 | Flagged as ANOMALY |
| **False Negatives** | 0 | Escaped detection |
