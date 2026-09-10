#ifndef TELEMETRY_H
#define TELEMETRY_H

#include <Arduino.h>
#include "config.h"

// ==============================================================================
// TelemetryWindow Data Structure
// Exactly defined data types with explicit alignment and zero dynamic memory.
// ==============================================================================
struct TelemetryWindow {
    // Window identifiers & Ground Truth
    uint32_t timestamp_ms;         // Uptime at window close (millis())
    uint32_t window_id;            // Monotonically increasing window index
    uint8_t  scenario_id;          // Active ScenarioID enum
    uint8_t  label;                // Ground truth: 0=NORMAL, 1=ANOMALY, 255=TRANSITION
    int8_t   wifi_rssi;            // Signal strength in dBm (-30 to -95 dBm)
    uint8_t  reconnect_count;      // Count of Wi-Fi reconnects in window
    uint16_t socket_errors;        // Count of socket failures in window
    uint16_t reserved1;            // Explicit alignment padding

    // Memory State (Exact Bytes)
    uint32_t free_heap;            // Free heap at window close (bytes)
    uint32_t min_free_heap;        // Lowest free heap recorded during window (bytes)
    int32_t  heap_delta;           // (free_heap_end - free_heap_start) in bytes
    uint32_t max_alloc_heap;       // Diagnostic: largest contiguous allocatable block

    // Application Socket / Transaction Volume
    uint16_t tx_count;             // Application socket write operations
    uint16_t rx_count;             // Application socket read operations
    uint16_t transaction_count;    // tx_count + rx_count
    uint16_t reserved2;            // Explicit alignment padding
    uint32_t tx_bytes;             // Total bytes written
    uint32_t rx_bytes;             // Total bytes read

    // Execution Timing & Continuous Dynamics
    float    loop_avg_ms;          // Average execution duration of application loop
    float    loop_max_ms;          // Worst-case blocking execution time in loop
    float    loop_jitter_ms;       // Standard deviation of loop execution time
    float    transaction_rate;     // Transactions per second (NOT IP packets)
    float    byte_rate;            // Total bytes processed per second (tx + rx)
    float    avg_inter_arrival_ms; // Mean time between consecutive socket transactions
    float    socket_duration_ms;   // Mean socket connection lifetime
};

class TelemetryEngine {
public:
    TelemetryEngine();
    void begin();
    
    // Window boundary controls
    void startWindow(uint32_t windowId, uint8_t scenarioId, uint8_t label);
    bool isWindowComplete() const;
    TelemetryWindow closeWindow();
    
    // Measurement instrumentation hooks
    void recordLoopStart();
    void recordLoopEnd();
    void recordSocketTx(uint32_t bytes);
    void recordSocketRx(uint32_t bytes);
    void recordSocketError();
    void recordSocketDuration(float durationMs);
    void recordWifiReconnect();

private:
    uint32_t window_start_ms;
    uint32_t current_window_id;
    uint8_t  current_scenario_id;
    uint8_t  current_label;
    
    // Memory watermarks
    uint32_t heap_at_start;
    uint32_t window_min_heap;
    
    // Traffic counters
    uint16_t count_tx;
    uint16_t count_rx;
    uint32_t bytes_tx_total;
    uint32_t bytes_rx_total;
    uint16_t error_count;
    uint8_t  reconnect_cnt;
    
    // Timing & Inter-arrival tracking
    uint32_t last_transaction_us;
    uint64_t total_inter_arrival_us;
    uint32_t inter_arrival_samples;
    
    float    total_socket_duration_ms;
    uint32_t socket_duration_samples;
    
    // Welford's streaming algorithm for loop latency
    uint32_t loop_start_us;
    uint32_t loop_count;
    double   loop_mean_us;
    double   loop_m2_us;
    float    loop_max_us;
};

extern TelemetryEngine Telemetry;

#endif // TELEMETRY_H
