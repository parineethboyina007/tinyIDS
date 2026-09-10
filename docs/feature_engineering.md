# TinyIDS Feature Engineering & Selection

## 1. Selected Feature Vector (10 Dimensions)
1. `transaction_rate`: Operations / second (`tx_count + rx_count / 5.0`).
2. `byte_rate`: Bytes / second throughput.
3. `free_heap`: Remaining dynamic memory at window end.
4. `heap_delta`: Signed memory allocation change (`free_heap_end - free_heap_start`).
5. `loop_avg_ms`: Mean application loop latency (Welford streaming algorithm).
6. `loop_max_ms`: Peak single-loop execution duration in window.
7. `loop_jitter_ms`: Streaming standard deviation of loop execution times.
8. `wifi_rssi`: Wi-Fi signal strength in dBm.
9. `avg_inter_arrival_ms`: Average interval between socket transactions.
10. `socket_errors`: Count of failed connections or write timeouts.

## 2. Eliminated Features & Rationale
* `tx_bytes` and `rx_bytes`: Highly redundant with `byte_rate`.
* `transaction_count`: Redundant with `transaction_rate`.
* TCP Flags (`syn_count`, `ack_count`): Require promiscuous sniffing which is prohibitive for microcontroller endpoints.
