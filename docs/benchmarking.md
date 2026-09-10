# TinyIDS Microcontroller Resource Benchmarks

Target: Arduino Nano ESP32 (ESP32-S3 @ 240 MHz)

| Subsystem | Metric | Measured Value | Allocation Limit |
| :--- | :--- | :---: | :---: |
| **Program Flash** | Total Binary Size | **708,477 bytes** | 3,145,728 bytes (22.5%) |
| **Dynamic SRAM** | Global Static Variables | **56,452 bytes** | 327,680 bytes (17.2%) |
| **Available Heap**| Free Dynamic Memory | **271,228 bytes** | ~271 KB free for user buffers |
| **Telemetry Struct**| Size per Window | **76 bytes** | Compile-time `static_assert` |
| **Inference Time**| Execution Duration | **< 50 microseconds** | Measured via `micros()` |
| **Window Processing**| Aggregation + Inference | **< 200 microseconds** | < 0.005% of 5000 ms window |
