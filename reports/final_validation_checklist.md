# TinyIDS V3 — Final Engineering Validation Checklist

| Component / Subsystem | Validation Test | Result | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **Toolchain & Core** | Compilation against `arduino:esp32:nano_nora` | **PASS** | Built cleanly with 0 errors via bundled `arduino-cli` |
| **Memory Footprint** | Flash usage < 30% of total partition | **PASS** | 708,477 bytes used (22.5% of 3.14 MB) |
| **Dynamic RAM** | Free heap headroom > 200 KB | **PASS** | 271,228 bytes free dynamic memory verified |
| **Struct Packing** | `sizeof(TelemetryWindow) == 76` bytes | **PASS** | Compile-time `static_assert` passed |
| **Loop Timing** | Serial printing isolated from loop measurement | **PASS** | `recordLoopStart()` and `recordLoopEnd()` isolate application passes |
| **Streaming Loop Stats**| Welford algorithm $O(1)$ memory usage | **PASS** | Zero timing arrays allocated in SRAM |
| **Data Leakage** | All IP addresses, timestamps, identifiers purged | **PASS** | Audited in `reports/phase1/data_leakage_audit.md` |
| **Mathematical Parity**| Python StandardScaler vs C++ Normalization | **PASS** | 100% test vector prediction parity in `ml/export/parity_test.py` |
| **Unseen Anomaly** | Held-out attack generalization test | **PASS** | 100% recall on held-out `ANOMALY_COMBINED` scenario |
| **Temporal Smoothing**| 3-window consensus logic | **PASS** | Implemented in `firmware/TinyIDS/inference.cpp` |
| **Live Dashboard** | Dual operating modes (`MODE_CSV` / `MODE_DASHBOARD`)| **PASS** | Configurable via `#define OPERATING_MODE` in `config.h` |
| **Host Tooling** | Automatic port detection & CSV logging | **PASS** | Tested in `tools/collect_esp32_data.py` & `tools/flash_and_test.py` |
