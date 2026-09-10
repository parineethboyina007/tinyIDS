#include "serial_logger.h"
#include "config.h"

SerialLogger Logger;

SerialLogger::SerialLogger() {
    current_mode = DEFAULT_OPERATING_MODE;
    header_printed = false;
}

void SerialLogger::begin() {
    Serial.begin(SERIAL_BAUD_RATE);
    
    unsigned long start = millis();
    while (!Serial && (millis() - start < USB_CDC_WAIT_MS)) {
        delay(10);
    }
    
    if (current_mode == MODE_DASHBOARD) {
        printBootBanner();
    } else {
        printCsvHeader();
    }
}

void SerialLogger::setMode(uint8_t mode) {
    current_mode = mode;
    if (current_mode == MODE_CSV) {
        header_printed = false;
        printCsvHeader();
    } else {
        Serial.println("\n[INFO] Switched to LIVE DASHBOARD mode. Type 'HELP' for interactive commands.\n");
    }
}

void SerialLogger::printBootBanner() {
    Serial.println("\n==================================================");
    Serial.println("  TinyIDS v" FIRMWARE_VERSION " — On-Device Behavioral IDS");
    Serial.println("  Target: Arduino Nano ESP32 (ESP32-S3 @ 240 MHz)");
    Serial.println("==================================================");
    Serial.printf("Chip Model     : %s (Rev %d)\n", ESP.getChipModel(), ESP.getChipRevision());
    Serial.printf("CPU Frequency  : %u MHz\n", ESP.getCpuFreqMHz());
    Serial.printf("Flash Capacity : %u bytes (%.1f MB)\n", ESP.getFlashChipSize(), ESP.getFlashChipSize() / (1024.0f * 1024.0f));
    Serial.printf("Free SRAM Heap : %u bytes\n", ESP.getFreeHeap());
    Serial.println("Interactive CLI: READY. Type 'HELP' to list scenario commands.");
    Serial.println("==================================================\n");
}

void SerialLogger::printHelp() {
    Serial.println("\n=== TinyIDS Interactive Serial Commands ===");
    Serial.println("  HELP             : Print this command menu");
    Serial.println("  STATUS           : Print immediate device health snapshot");
    Serial.println("  DASHBOARD        : Switch to live visual monitoring dashboard");
    Serial.println("  CSV              : Switch to machine-readable CSV streaming");
    Serial.println("  IDLE             : Switch to SCENARIO_NORMAL_IDLE");
    Serial.println("  PERIODIC         : Switch to SCENARIO_NORMAL_PERIODIC");
    Serial.println("  VARIABLE         : Switch to SCENARIO_NORMAL_VARIABLE");
    Serial.println("  HIGH_RATE        : Switch to ANOMALY_HIGH_RATE (traffic flood)");
    Serial.println("  BURST            : Switch to ANOMALY_BURST (rapid packet bursts)");
    Serial.println("  CONNECTION       : Switch to ANOMALY_CONNECTION_STRESS");
    Serial.println("  COMPUTE          : Switch to ANOMALY_COMPUTE (CPU starvation)");
    Serial.println("  MEMORY           : Switch to ANOMALY_MEMORY (heap allocation pressure)");
    Serial.println("  COMBINED         : Switch to ANOMALY_COMBINED (traffic + compute)");
    Serial.println("===========================================\n");
}

void SerialLogger::printCsvHeader() {
    if (!header_printed) {
        Serial.println("timestamp_ms,window_id,scenario,label,free_heap,min_free_heap,heap_delta,max_alloc_heap,loop_avg_ms,loop_max_ms,loop_jitter_ms,wifi_rssi,tx_count,rx_count,tx_bytes,rx_bytes,transaction_rate,byte_rate,avg_inter_arrival_ms,transaction_count,reconnect_count,socket_errors,socket_duration_ms");
        header_printed = true;
    }
}

void SerialLogger::logWindow(const TelemetryWindow& win, const InferenceResult& ml) {
    if (current_mode == MODE_DASHBOARD) {
        Serial.println("==================================================");
        Serial.println("       TinyIDS — On-Device Behavioral IDS         ");
        Serial.println("==================================================");
        Serial.printf("Window ID       : %u\n", win.window_id);
        Serial.printf("Uptime          : %u ms (%.1f s)\n", win.timestamp_ms, win.timestamp_ms / 1000.0f);
        Serial.printf("Active Scenario : %s [Ground Truth: %s]\n", getScenarioName(win.scenario_id), win.label == 1 ? "ANOMALY" : "NORMAL");
        Serial.println("--------------------------------------------------");
        Serial.printf("Transaction Rate: %.2f ops/s\n", win.transaction_rate);
        Serial.printf("Byte Throughput : %.1f B/s (%u bytes total)\n", win.byte_rate, win.tx_bytes + win.rx_bytes);
        Serial.printf("Free Heap       : %u bytes (Min: %u B | Delta: %d B)\n", win.free_heap, win.min_free_heap, win.heap_delta);
        Serial.printf("Loop Latency    : Avg: %.3f ms | Max: %.3f ms | Jitter: %.3f ms\n", win.loop_avg_ms, win.loop_max_ms, win.loop_jitter_ms);
        if (win.wifi_rssi == WIFI_RSSI_DISCONNECTED) {
            Serial.println("Wi-Fi Link      : OFFLINE (Operating Locally)");
        } else {
            Serial.printf("Wi-Fi RSSI      : %d dBm\n", win.wifi_rssi);
        }
        Serial.println("--------------------------------------------------");
        Serial.printf("PREDICTION      : %s\n", ml.prediction == 1 ? "!! ANOMALY DETECTED !!" : "NORMAL");
        Serial.printf("Confidence      : %.1f%%\n", ml.confidence * 100.0f);
        Serial.printf("Risk Score      : %u / 100 [%s]\n", ml.risk_score, ml.severity);
        Serial.printf("Temporal Smoothed: %s (2-of-3 window consensus)\n", ml.smoothed_prediction == 1 ? "ANOMALY" : "NORMAL");
        Serial.printf("Primary Cause   : %s\n", ml.primary_reason);
        Serial.printf("Inference Time  : %u us\n", ml.inference_time_us);
        Serial.println("==================================================\n");
    } else {
        // Pure CSV output
        Serial.print(win.timestamp_ms);
        Serial.print(',');
        Serial.print(win.window_id);
        Serial.print(',');
        Serial.print(getScenarioName(win.scenario_id));
        Serial.print(',');
        Serial.print(win.label);
        Serial.print(',');
        Serial.print(win.free_heap);
        Serial.print(',');
        Serial.print(win.min_free_heap);
        Serial.print(',');
        Serial.print(win.heap_delta);
        Serial.print(',');
        Serial.print(win.max_alloc_heap);
        Serial.print(',');
        Serial.print(win.loop_avg_ms, 4);
        Serial.print(',');
        Serial.print(win.loop_max_ms, 4);
        Serial.print(',');
        Serial.print(win.loop_jitter_ms, 4);
        Serial.print(',');
        Serial.print(win.wifi_rssi);
        Serial.print(',');
        Serial.print(win.tx_count);
        Serial.print(',');
        Serial.print(win.rx_count);
        Serial.print(',');
        Serial.print(win.tx_bytes);
        Serial.print(',');
        Serial.print(win.rx_bytes);
        Serial.print(',');
        Serial.print(win.transaction_rate, 4);
        Serial.print(',');
        Serial.print(win.byte_rate, 2);
        Serial.print(',');
        Serial.print(win.avg_inter_arrival_ms, 3);
        Serial.print(',');
        Serial.print(win.transaction_count);
        Serial.print(',');
        Serial.print(win.reconnect_count);
        Serial.print(',');
        Serial.print(win.socket_errors);
        Serial.print(',');
        Serial.println(win.socket_duration_ms, 3);
    }
}
