# TinyIDS V3 — Dataset Sampling & Partitioning Report

**Sampling Date**: 2026-09-08  
**Random Seed**: 42 (Deterministic)  
**Total Sample Size**: 100,000 records across 3 independent splits  

---

## 1. Sampling Strategy & Rationale

In the raw CICIoT2023 dataset, benign traffic accounts for only **2.36%** of training data, while volumetric attacks represent **97.64%**. A naive classifier predicting "Attack" on every instance would report 97.64% accuracy while being completely non-functional as an intrusion detection system.

To build an experimentally valid, defensible baseline without data distortion:
1. **Preserve Split Isolation**:
   Samples are drawn exclusively from within their respective official partitions:
   - `CICIOT23/train/train.csv` -> `dataset/processed/sampled_train.csv` (70,000 records)
   - `CICIOT23/validation/validation.csv` -> `dataset/processed/sampled_validation.csv` (15,000 records)
   - `CICIOT23/test/test.csv` -> `dataset/processed/sampled_test.csv` (15,000 records)
   Zero cross-split leakage or shuffling occurred across file boundaries.
2. **Balanced Binary Formulation**:
   A 50% Benign (NORMAL = 0) vs. 50% Attack (ANOMALY = 1) ratio was enforced in each split.
3. **Class Diversity & Rare Attack Preservation**:
   Within the attack quota (35,000 in train, 7,500 in val/test), samples were allocated proportionally across all 33 attack classes with a minimum floor quota. Rare attacks like `Uploading_Attack`, `Recon-PingSweep`, `Backdoor_Malware`, `XSS`, and `SqlInjection` are preserved rather than dropped.
4. **Streaming Algorithm**:
   Streaming reservoir sampling with chunked CSV reading (250,000 rows/chunk) was used, requiring only ~40 MB RAM maximum.

---

## 2. Sampled Split Verification

| Split Name | Original Raw Rows | Sampled Records | Benign (`NORMAL = 0`) | Attack (`ANOMALY = 1`) | Classes Preserved | Output File |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Train** | 5,491,971 | **70,000** | 35,000 (50.0%) | 35,000 (50.0%) | **34 / 34 (100%)** | `dataset/processed/sampled_train.csv` |
| **Validation** | 1,176,851 | **15,000** | 7,500 (50.0%) | 7,500 (50.0%) | **34 / 34 (100%)** | `dataset/processed/sampled_validation.csv` |
| **Test** | 1,176,851 | **15,000** | 7,500 (50.0%) | 7,500 (50.0%) | **34 / 34 (100%)** | `dataset/processed/sampled_test.csv` |
| **Total** | **7,845,673** | **100,000** | **50,000 (50.0%)** | **50,000 (50.0%)** | **34 / 34 (100%)** | Ready for Model Benchmarking |
