# TinyIDS Datasets: Public vs. Hardware Schema

## 1. CICIoT2023 (Public Research Baseline)
* **Source**: Canadian Institute for Cybersecurity (UNB).
* **Nature**: 7,845,673 network flow records captured via external network tap.
* **Role in TinyIDS**: Feasibility benchmark demonstrating that 14 endpoint-observable features retain 99.19% of the F1-score of 44 sniffer features.

## 2. ESP32 Real Hardware Dataset
* **Source**: Arduino Nano ESP32 runtime telemetry.
* **Aggregation**: 5000 ms fixed window.
* **Attributes**: 23 total columns (10 primary ML features, memory watermarks, RF state).
* **Role in TinyIDS**: The ground truth dataset for on-device TinyML model training and deployment.
