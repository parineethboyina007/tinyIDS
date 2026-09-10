# TinyIDS V3 — Final Measured System Results

| System / ML Dimension | Metric | Measured Value | Scientific Evaluation |
| :--- | :--- | :---: | :--- |
| **Target Hardware** | Board | **Arduino Nano ESP32** | u-blox NORA-W106 module |
| **Microcontroller** | SoC | **ESP32-S3** | Xtensa dual-core LX7 @ 240 MHz |
| **Memory Capacity** | Internal SRAM / Flash | **512 KB / 16 MB** | 3.14 MB allocated app partition |
| **Telemetry Vector**| Features Count | **10 Features** | Endpoint rates, timing, heap, RF |
| **Firmware Memory** | Program Flash Usage | **708,477 bytes (22.5%)** | 708 KB footprint; 2.43 MB free |
| **Firmware Memory** | Static SRAM Usage | **56,452 bytes (17.2%)** | 271,228 bytes dynamic heap free |
| **Window Struct** | Memory Footprint | **76 bytes** | Compile-time `static_assert` verified |
| **Model Candidate** | Architecture | **Decision Tree** | Pure C++ branching evaluation |
| **Model Size** | Serialized Footprint | **1.5 KB** | Less than 0.5% of MCU RAM |
| **Detection Quality**| Test F1-Score | **99.16%** | High balance of precision & recall |
| **Detection Quality**| Test Precision | **98.33%** | Very low false alarm rate |
| **Detection Quality**| Test Recall | **100.00%** | Zero missed anomalies on test set |
| **Security Metric** | False Positive Rate | **3.23%** (Single Window) | Raw single-window baseline |
| **Security Metric** | FPR (Temporal Smoothed)| **< 0.50%** (3-Window) | 2-of-3 majority consensus |
| **Unseen Generalization**| Held-Out Anomaly Recall| **100.00%** (66 / 66) | Detected `ANOMALY_COMBINED` without prior training |
| **Inference Latency**| Execution Duration | **< 50 microseconds** | Measured via `micros()` on ESP32-S3 |
| **Detection Latency**| End-to-End Decision | **~5.001 seconds** | 5000 ms window + inference |
