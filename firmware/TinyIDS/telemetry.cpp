#include "telemetry.h"
#include <WiFi.h>
#include <esp_heap_caps.h>
#include <math.h>

TelemetryEngine Telemetry;

TelemetryEngine::TelemetryEngine() {
    window_start_ms = 0;
    current_window_id = 0;
    current_scenario_id = 0;
    current_label = 0;
    heap_at_start = 0;
    window_min_heap = 0xFFFFFFFF;
    count_tx = 0;
    count_rx = 0;
    bytes_tx_total = 0;
    bytes_rx_total = 0;
    error_count = 0;
    reconnect_cnt = 0;
    last_transaction_us = 0;
    total_inter_arrival_us = 0;
    inter_arrival_samples = 0;
    total_socket_duration_ms = 0.0f;
    socket_duration_samples = 0;
    loop_start_us = 0;
    loop_count = 0;
    loop_mean_us = 0.0;
    loop_m2_us = 0.0;
    loop_max_us = 0.0f;
}

void TelemetryEngine::begin() {
    window_start_ms = millis();
    heap_at_start = ESP.getFreeHeap();
    window_min_heap = heap_at_start;
}

void TelemetryEngine::startWindow(uint32_t windowId, uint8_t scenarioId, uint8_t label) {
    window_start_ms = millis();
    current_window_id = windowId;
    current_scenario_id = scenarioId;
    current_label = label;
    
    heap_at_start = ESP.getFreeHeap();
    window_min_heap = heap_at_start;
    
    count_tx = 0;
    count_rx = 0;
    bytes_tx_total = 0;
    bytes_rx_total = 0;
    error_count = 0;
    reconnect_cnt = 0;
    
    last_transaction_us = micros();
    total_inter_arrival_us = 0;
    inter_arrival_samples = 0;
    
    total_socket_duration_ms = 0.0f;
    socket_duration_samples = 0;
    
    loop_count = 0;
    loop_mean_us = 0.0;
    loop_m2_us = 0.0;
    loop_max_us = 0.0f;
}

bool TelemetryEngine::isWindowComplete() const {
    return (millis() - window_start_ms) >= WINDOW_DURATION_MS;
}

TelemetryWindow TelemetryEngine::closeWindow() {
    TelemetryWindow win;
    
    uint32_t now_ms = millis();
    float window_sec = (float)(now_ms - window_start_ms) / 1000.0f;
    if (window_sec <= 0.001f) window_sec = 0.001f;
    
    win.timestamp_ms = now_ms;
    win.window_id = current_window_id;
    win.scenario_id = current_scenario_id;
    win.label = current_label;
    
    // Wi-Fi RF state: uses WIFI_RSSI_DISCONNECTED sentinel (-127) when offline
    if (WiFi.status() == WL_CONNECTED) {
        win.wifi_rssi = (int8_t)WiFi.RSSI();
    } else {
        win.wifi_rssi = (int8_t)WIFI_RSSI_DISCONNECTED;
    }
    win.reconnect_count = reconnect_cnt;
    win.socket_errors = error_count;
    win.reserved1 = 0;
    
    // Memory state
    uint32_t current_heap = ESP.getFreeHeap();
    if (current_heap < window_min_heap) window_min_heap = current_heap;
    win.free_heap = current_heap;
    win.min_free_heap = window_min_heap;
    win.heap_delta = (int32_t)current_heap - (int32_t)heap_at_start;
    win.max_alloc_heap = ESP.getMaxAllocHeap();
    
    // Traffic volume
    win.tx_count = count_tx;
    win.rx_count = count_rx;
    win.transaction_count = count_tx + count_rx;
    win.reserved2 = 0;
    win.tx_bytes = bytes_tx_total;
    win.rx_bytes = bytes_rx_total;
    
    // Continuous Rates (Units: per second)
    win.transaction_rate = (float)win.transaction_count / window_sec;
    win.byte_rate = (float)(bytes_tx_total + bytes_rx_total) / window_sec;
    
    // Inter-arrival calculation
    if (inter_arrival_samples > 0) {
        win.avg_inter_arrival_ms = (float)(total_inter_arrival_us / inter_arrival_samples) / 1000.0f;
    } else {
        win.avg_inter_arrival_ms = (float)(WINDOW_DURATION_MS);
    }
    
    // Socket duration
    if (socket_duration_samples > 0) {
        win.socket_duration_ms = total_socket_duration_ms / (float)socket_duration_samples;
    } else {
        win.socket_duration_ms = 0.0f;
    }
    
    // Loop latency metrics (Welford's streaming results)
    if (loop_count > 0) {
        win.loop_avg_ms = (float)(loop_mean_us / 1000.0);
        win.loop_max_ms = (float)(loop_max_us / 1000.0f);
        if (loop_count > 1) {
            double variance_us2 = loop_m2_us / (double)(loop_count - 1);
            win.loop_jitter_ms = (float)(sqrt(variance_us2) / 1000.0);
        } else {
            win.loop_jitter_ms = 0.0f;
        }
    } else {
        win.loop_avg_ms = 0.0f;
        win.loop_max_ms = 0.0f;
        win.loop_jitter_ms = 0.0f;
    }
    
    return win;
}

void TelemetryEngine::recordLoopStart() {
    loop_start_us = micros();
    uint32_t h = ESP.getFreeHeap();
    if (h < window_min_heap) {
        window_min_heap = h;
    }
}

void TelemetryEngine::recordLoopEnd() {
    uint32_t dt_us = micros() - loop_start_us;
    loop_count++;
    
    double delta = (double)dt_us - loop_mean_us;
    loop_mean_us += delta / (double)loop_count;
    double delta2 = (double)dt_us - loop_mean_us;
    loop_m2_us += delta * delta2;
    
    if ((float)dt_us > loop_max_us) {
        loop_max_us = (float)dt_us;
    }
}

void TelemetryEngine::recordSocketTx(uint32_t bytes) {
    count_tx++;
    bytes_tx_total += bytes;
    
    uint32_t now_us = micros();
    if (last_transaction_us > 0 && now_us > last_transaction_us) {
        total_inter_arrival_us += (now_us - last_transaction_us);
        inter_arrival_samples++;
    }
    last_transaction_us = now_us;
}

void TelemetryEngine::recordSocketRx(uint32_t bytes) {
    count_rx++;
    bytes_rx_total += bytes;
    
    uint32_t now_us = micros();
    if (last_transaction_us > 0 && now_us > last_transaction_us) {
        total_inter_arrival_us += (now_us - last_transaction_us);
        inter_arrival_samples++;
    }
    last_transaction_us = now_us;
}

void TelemetryEngine::recordSocketError() {
    error_count++;
}

void TelemetryEngine::recordSocketDuration(float durationMs) {
    total_socket_duration_ms += durationMs;
    socket_duration_samples++;
}

void TelemetryEngine::recordWifiReconnect() {
    reconnect_cnt++;
}
