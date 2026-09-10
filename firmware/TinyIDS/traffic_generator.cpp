#include "traffic_generator.h"
#include "telemetry.h"
#include <WiFi.h>

TrafficGenerator TrafficGen;

TrafficGenerator::TrafficGenerator() {
    last_action_ms = 0;
    variable_interval_ms = 500;
    memory_stress_ptr = nullptr;
    memory_stress_size = 0;
}

void TrafficGenerator::begin() {
    last_action_ms = millis();
}

void TrafficGenerator::performSocketExchange(uint16_t payloadBytes) {
    uint32_t t_start = millis();
    
    // Generate synthetic application-level transaction
    // If connected to network, attempts lightweight socket connection;
    // Otherwise performs internal network-stack loopback simulation
    if (WiFi.status() == WL_CONNECTED) {
        WiFiClient client;
        client.setTimeout(200); // 200 ms timeout
        if (client.connect(TEST_SERVER_HOST, TEST_SERVER_PORT)) {
            // Write payload
            char dummy[128];
            memset(dummy, 'A', sizeof(dummy));
            uint16_t written = 0;
            while (written < payloadBytes) {
                uint16_t to_write = (payloadBytes - written > sizeof(dummy)) ? sizeof(dummy) : (payloadBytes - written);
                client.write((const uint8_t*)dummy, to_write);
                written += to_write;
            }
            Telemetry.recordSocketTx(payloadBytes);
            
            // Read response chunk if available
            uint32_t r_start = millis();
            uint32_t bytes_read = 0;
            while (client.connected() && (millis() - r_start < 50)) {
                int avail = client.available();
                if (avail > 0) {
                    int r = client.read((uint8_t*)dummy, avail > (int)sizeof(dummy) ? sizeof(dummy) : avail);
                    if (r > 0) bytes_read += r;
                }
            }
            if (bytes_read > 0) {
                Telemetry.recordSocketRx(bytes_read);
            }
            client.stop();
            Telemetry.recordSocketDuration((float)(millis() - t_start));
        } else {
            Telemetry.recordSocketError();
        }
    } else {
        // Fallback endpoint application-level simulation (e.g. offline bench)
        Telemetry.recordSocketTx(payloadBytes);
        delayMicroseconds(200);
        Telemetry.recordSocketRx(payloadBytes / 2);
        Telemetry.recordSocketDuration(1.5f);
    }
}

void TrafficGenerator::performSafeComputation(uint32_t targetTimeMs) {
    if (targetTimeMs > MAX_COMPUTE_CHUNK_MS) {
        targetTimeMs = MAX_COMPUTE_CHUNK_MS;
    }
    uint32_t start_us = micros();
    uint32_t target_us = targetTimeMs * 1000;
    
    volatile uint32_t val = 12345;
    while (micros() - start_us < target_us) {
        // Compute pseudo-random hashing / arithmetic steps
        val ^= val << 13;
        val ^= val >> 17;
        val ^= val << 5;
    }
}

void TrafficGenerator::executeIdle() {
    // Minimal background maintenance; 10 ms sleep
    delay(10);
}

void TrafficGenerator::executeNormalPeriodic() {
    uint32_t now = millis();
    // Regular transactions every 1000 ms, payload 128 bytes
    if (now - last_action_ms >= 1000) {
        last_action_ms = now;
        performSocketExchange(128);
    }
    delay(5);
}

void TrafficGenerator::executeNormalVariable() {
    uint32_t now = millis();
    // Randomized intervals (300 to 1200 ms) and randomized payload (64 to 512 bytes)
    if (now - last_action_ms >= variable_interval_ms) {
        last_action_ms = now;
        uint16_t random_bytes = (uint16_t)(64 + (random(0, 8) * 64));
        performSocketExchange(random_bytes);
        variable_interval_ms = (uint32_t)random(300, 1200);
    }
    delay(5);
}

void TrafficGenerator::executeAnomalyHighRate() {
    uint32_t now = millis();
    // High transaction frequency (every 50 ms)
    if (now - last_action_ms >= 50) {
        last_action_ms = now;
        performSocketExchange(256);
    }
}

void TrafficGenerator::executeAnomalyBurst() {
    uint32_t now = millis();
    // Burst: 10 back-to-back transactions every 2500 ms
    if (now - last_action_ms >= 2500) {
        last_action_ms = now;
        for (int i = 0; i < 8; i++) {
            performSocketExchange(128);
            delayMicroseconds(500);
        }
    }
    delay(5);
}

void TrafficGenerator::executeAnomalyConnectionStress() {
    uint32_t now = millis();
    // Rapid socket connection attempts (every 100 ms)
    if (now - last_action_ms >= 100) {
        last_action_ms = now;
        performSocketExchange(32);
    }
}

void TrafficGenerator::executeAnomalyCompute() {
    // Inject CPU-heavy workloads (15-20 ms blocks) that alter loop latency
    performSafeComputation(18);
    delay(2);
}

void TrafficGenerator::executeAnomalyMemory() {
    // Safely allocate a temporary 32 KB buffer if heap allows, touch it, and free it
    if (ESP.getFreeHeap() > (MIN_SAFE_FREE_HEAP + 32768)) {
        if (!memory_stress_ptr) {
            memory_stress_size = 32768;
            memory_stress_ptr = (uint8_t*)malloc(memory_stress_size);
            if (memory_stress_ptr) {
                memset(memory_stress_ptr, 0xAA, memory_stress_size);
            }
        } else {
            // Retain memory for a brief interval then free
            free(memory_stress_ptr);
            memory_stress_ptr = nullptr;
        }
    }
    delay(50);
}

void TrafficGenerator::executeAnomalyCombined() {
    // Fuses High-Rate network traffic + CPU compute stress
    uint32_t now = millis();
    if (now - last_action_ms >= 80) {
        last_action_ms = now;
        performSocketExchange(256);
    }
    performSafeComputation(12);
}
