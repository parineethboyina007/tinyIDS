# TinyIDS V3 — Complete Viva & Technical Defense Guide

This document prepares the engineer to defend every aspect of TinyIDS across Embedded Systems, Machine Learning, Cybersecurity, and TinyML.

---

### Section 1: Embedded Systems & Target Hardware

**Q1: What microcontroller powers the Arduino Nano ESP32?**  
*Answer*: The Espressif ESP32-S3 (Xtensa dual-core 32-bit LX7 running at up to 240 MHz, with 512 KB internal SRAM and 16 MB external QSPI flash).

**Q2: What is the difference between Flash and RAM on the ESP32?**  
*Answer*: Flash is non-volatile memory storing firmware instructions, static assets, and read-only model parameters. RAM (SRAM) is volatile memory used at runtime for global variables, dynamic heap allocations, execution stack, and ML tensor buffers.

**Q3: What is the difference between Heap and Stack?**  
*Answer*: The stack stores local function variables and call frames, managed automatically in LIFO order. The heap is dynamic memory allocated via `malloc()` or `new`. In embedded systems, excessive heap allocation causes memory fragmentation and unpredictable out-of-memory crashes.

**Q4: How does native USB CDC differ from a standard UART bridge chip?**  
*Answer*: Traditional boards use an external USB-to-UART chip (like CH340 or FTDI). The Nano ESP32's ESP32-S3 has an internal USB-OTG peripheral handling USB CDC directly in firmware. Calling an unbounded `while (!Serial);` can hang the MCU if powered from a standalone adapter, so TinyIDS implements a 3000 ms bounded timeout.

**Q5: Why is `micros()` used instead of `millis()` for loop latency?**  
*Answer*: An optimized microcontroller loop typically executes in 50–300 microseconds. Using `millis()` would yield 0 ms for most iterations, causing extreme quantization distortion.

---

### Section 2: Cybersecurity & Threat Modeling

**Q6: What is an IDS vs. an IPS?**  
*Answer*: An Intrusion Detection System (IDS) passively monitors telemetry, analyzes patterns, and alerts on anomalous behavior. An Intrusion Prevention System (IPS) actively sits inline to drop packets or terminate malicious connections. TinyIDS is an endpoint behavioral IDS.

**Q7: What is Signature-Based Detection vs. Behavioral Anomaly Detection?**  
*Answer*: Signature detection matches exact known patterns (e.g., known malware hashes or attack byte sequences). It cannot detect zero-day or modified attacks. Behavioral anomaly detection models baseline legitimate behavior and detects statistical deviations, enabling detection of novel and unseen attack variants.

**Q8: Why can't an Arduino Nano ESP32 run a full promiscuous packet sniffer?**  
*Answer*: Promiscuous packet sniffing requires receiving and parsing every Layer 2/3 frame on the Wi-Fi channel. At 240 MHz with 512 KB RAM, processing high-throughput network streams would saturate the CPU, drop frames, and starve the actual IoT application. TinyIDS instead leverages lightweight **endpoint telemetry**.

**Q9: What is the difference between False Positives and False Negatives in security?**  
*Answer*: A False Positive (FP) flags legitimate user activity as an attack, causing alert fatigue. A False Negative (FN) misses an active intrusion. For safety-critical systems, minimizing False Negatives (high Recall) is vital while keeping False Positive Rate (FPR) strictly below 1%.

**Q10: What is the concept of a Risk Score (0–100)?**  
*Answer*: Rather than outputting a brittle binary 0 or 1, TinyIDS maps model confidence, dominant feature deviations, and temporal persistence into a continuous 0–100 risk score categorized as LOW (0–29), MEDIUM (30–59), HIGH (60–79), and CRITICAL (80–100).

---

### Section 3: Machine Learning & Preprocessing

**Q11: What is the "Accuracy Paradox" in cybersecurity datasets?**  
*Answer*: In datasets like CICIoT2023, attacks represent 97.64% and benign traffic represents only 2.36%. A dummy model predicting "Attack" on every sample achieves 97.64% accuracy while failing 100% of the time on benign traffic. F1-score, Precision, Recall, and FPR must be used.

**Q12: Why did Decision Tree outperform Logistic Regression on reduced features?**  
*Answer*: On reduced endpoint features, attack boundaries are nonlinear combinations of rates and timings (e.g., `Rate > X AND Tot_size < Y`). Linear hyperplanes in Logistic Regression cannot separate these clusters, causing its False Positive Rate to surge to nearly 11%.

**Q13: Why wasn't Random Forest selected for final deployment despite high accuracy?**  
*Answer*: Random Forest required 50 trees and over 18,000 nodes, totaling ~1.48 MB of memory. On an ESP32 with 512 KB SRAM, this is impractical. A single Decision Tree achieved 99.19% F1 at just 10 KB—a negligible 0.08% difference for a 148x reduction in memory!

**Q14: How is preprocessing parity guaranteed between Python and C++?**  
*Answer*: The exact training mean ($\mu$) and standard deviation ($\sigma$) from scikit-learn's `StandardScaler` are exported into JSON and compiled into firmware constants. Both environments compute identical Z-scores.

**Q15: What is Data Leakage and how did you prevent it?**  
*Answer*: Data leakage occurs when training data contains artifacts (IP addresses, scenario-revealing timestamps) that artificially inflate test scores. We audited all features, purged identifiers, strictly preserved official split boundaries, and enforced a transition-window discard policy.

---

### Section 4: TinyML & Embedded Deployment

**Q16: What is TinyML?**  
*Answer*: TinyML is the deployment of machine learning algorithms onto ultra-low-power, resource-constrained microcontrollers (MCWs) consuming milliwatts of power and kilobytes of memory.

**Q17: What is the difference between Inference Latency and Detection Latency?**  
*Answer*: Inference latency is the microsecond execution duration required to evaluate a feature vector through the model (~10–50 $\mu$s). Detection latency is the total elapsed time from when an anomaly begins until TinyIDS confirms it (5.0s window + inference = ~5.001s).

**Q18: What is Temporal Smoothing?**  
*Answer*: Evaluating single 5-second windows in isolation risks triggering false alarms from transient network spikes. TinyIDS maintains a 3-window ring buffer and requires a 2-of-3 majority consensus, drastically lowering False Positive Rates.

**Q19: What is Concept Drift vs. Domain Shift?**  
*Answer*: Domain shift occurs when deployment environment conditions differ from training data (e.g., different Wi-Fi routers). Concept drift occurs when normal behavior evolves over time (e.g., firmware updates or new sensor reporting schedules).

**Q20: What are the main limitations of TinyIDS?**  
*Answer*: TinyIDS monitors endpoint behavioral proxies. It cannot detect stealthy zero-payload memory exploits that do not alter CPU timing, heap allocations, or socket transaction frequencies, nor does it inspect encrypted application payloads.
