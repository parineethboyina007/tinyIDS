# TinyIDS V3 — Data Leakage & Feature Integrity Audit

**Audit Date**: 2026-09-08  
**Scope**: CICIoT2023 (`train.csv`, `test.csv`, `validation.csv`) & TON_IoT (`ton-iot.csv`)  
**Lead Engineer**: TinyIDS Cybersecurity & ML Team  

---

## 1. Executive Summary

Data leakage occurs when training data contains artifacts or indicators that artificially inflate model performance during offline testing but fail to generalize to real-world embedded deployment. A rigorous audit was performed across all datasets in the workspace to identify and eliminate potential leakage vectors before baseline model training.

---

## 2. Audit Checklist & Findings

| Audit Check | Status | Finding in CICIoT2023 | Finding in TON_IoT | Remediation Action |
| :--- | :---: | :--- | :--- | :--- |
| **Source / Destination IP Leakage** | **CLEAN (CIC) / LEAKAGE (TON)** | No IP columns exist in CICIoT2023. | Contains `src_ip` and `dst_ip` (e.g., `192.168.1.31` indicates attacker). | Exclude IP columns completely. Do not train on TON-IoT sample. |
| **Source / Destination Port Leakage** | **CLEAN (CIC) / LEAKAGE (TON)** | No port columns exist in CICIoT2023. | Contains `src_port` (ephemeral port) and `dst_port` (service port). | Exclude ephemeral ports from ML models. |
| **Scenario-Revealing Timestamps** | **CLEAN (CIC) / LEAKAGE (TON)** | Only relative intervals (`flow_duration`, `Duration`, `IAT`). No wall-clock epochs. | Contains monotonic epoch timestamp `ts` (`1554198358` to `1556203822`). | Exclude `ts` column from any model training. |
| **Label Encoding in Features** | **CLEAN** | Feature names and values are purely statistical measurements. No encoded target. | Target is cleanly separated into `label` and `type`. | Verified. |
| **Zero-Variance (Constant) Columns** | **ACTION REQUIRED** | `Telnet` (0.0) and `IRC` (0.0) are constant zero across all 5.49M train rows. | Columns like `dns_qclass`, `dns_qtype` contain '-' placeholders. | Drop `Telnet` and `IRC` from all feature sets immediately. |
| **Near-Zero Variance / Metadata** | **CLEANED** | `IPv` and `LLC` are 99.99% 1.0 (Ethernet framing). `Weight` is a CICFlowMeter artifact. | Multiple columns with 100% '-' placeholders. | Removed from reduced feature sets (`SET B` and `SET C`). |
| **Split Contamination / Overlap** | **CONTROLLED** | Pre-partitioned `train.csv` (70%), `test.csv` (15%), and `validation.csv` (15%) are preserved. | Only 19 sample rows exist. | Strict split preservation. Sampler pulls independently from train, val, and test splits without merging. |
| **Identical Feature Duplicates** | **DETECTED IN VOLUMETRIC FLOODS** | Within a 50,000-row train chunk, 19 exact duplicates (0.04%) were found, typical of high-rate ICMP/UDP flood attacks where packet size and protocol are identical. | 0 duplicate rows in sample. | Normal for volumetric packet bursts. Feature deduplication is noted; stratified sampling preserves class diversity. |

---

## 3. Data Leakage Remediation Decisions

1. **Purge Zero-Variance Columns**:
   `Telnet` and `IRC` are dropped from all experimental feature sets (`SET A`, `SET B`, `SET C`).
2. **Eliminate Internal Extractor Artifacts**:
   `Weight` (an internal CICFlowMeter decaying window factor) is retained in `SET A` only to benchmark full raw dataset reproduction, but strictly purged from `SET B` and `SET C`.
3. **Strict Partitioning**:
   We preserve the original Canadian Institute for Cybersecurity split partition:
   - Training samples are drawn exclusively from `CICIOT23/train/train.csv`.
   - Validation samples are drawn exclusively from `CICIOT23/validation/validation.csv`.
   - Test evaluation is drawn exclusively from `CICIOT23/test/test.csv`.
   Under no circumstances are these files concatenated and randomly reshuffled, preventing any temporal or burst correlation leakage.
4. **TON_IoT Guardrail**:
   `ton-iot.csv` contains only 19 records and carries obvious IP and timestamp leakages. It is marked as `TON_IOT_LOCAL_SAMPLE_NOT_SUFFICIENT_FOR_TRAINING` and quarantined from all model training pipelines.
