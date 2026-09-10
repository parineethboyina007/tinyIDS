# TinyIDS Technical Limitations & Honest Boundaries

1. **Endpoint Observation Scope**: TinyIDS observes endpoint socket transactions and hardware state. It does not inspect external network traffic passing between other hosts on the subnet.
2. **Encrypted Payloads**: TinyIDS monitors traffic volume and timing dynamics; it does not decrypt or inspect HTTPS/TLS packet contents.
3. **Controlled Synthetic Anomalies**: Scenarios are controlled behavioral stress tests, not live zero-day weaponized exploits.
4. **RF Environment Variability**: Natural Wi-Fi signal fluctuations can introduce variance in RSSI and latency.
