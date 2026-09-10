# TinyIDS On-Device Embedded Deployment

## 1. Model Representation
* **Architecture**: Branch-optimized C++ Decision Tree (`firmware/TinyIDS/model_tree.h`).
* **Memory Footprint**: 1.5 KB serialized; embedded directly into Flash code space.
* **Runtime Dynamic Heap Cost**: **0 bytes** (zero heap allocation during inference).

## 2. Real-Time Inference Loop
1. Every 5000 ms, `Telemetry.closeWindow()` aggregates telemetry.
2. `TinyML.predict(win)` evaluates the feature vector in `< 50 microseconds`.
3. 3-window temporal consensus determines final alert status.
4. Outputs either machine-readable CSV (`MODE_CSV`) or formatted dashboard (`MODE_DASHBOARD`).
