# TinyIDS Machine Learning Pipeline

```text
Raw ESP32 Telemetry CSV
           │
           ▼
Transition Window Discard (label == 255)
           │
           ▼
Session-Aware Data Partitioning
(Train: Session 01 | Val: Session 02 | Test: Session 03)
           │
           ▼
Z-Score Standardization: (x - mean) / std
(Fitted on Train; Exported to C++ Header)
           │
           ▼
Model Training & Comparison
(Decision Tree, Random Forest, Logistic Regression, MLP)
           │
           ▼
Model Selection (F1-score, Memory Size, Inference Latency)
           │
           ▼
C++ Transpilation & Parity Verification
(model_tree.h & test_vectors.json)
```
