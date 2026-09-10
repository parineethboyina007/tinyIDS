#ifndef TRAFFIC_GENERATOR_H
#define TRAFFIC_GENERATOR_H

#include <Arduino.h>
#include <WiFiClient.h>
#include "config.h"

class TrafficGenerator {
public:
    TrafficGenerator();
    void begin();
    
    // Workload executors called within main loop()
    void executeIdle();
    void executeNormalPeriodic();
    void executeNormalVariable();
    void executeAnomalyHighRate();
    void executeAnomalyBurst();
    void executeAnomalyConnectionStress();
    void executeAnomalyCompute();
    void executeAnomalyMemory();
    void executeAnomalyCombined();

private:
    uint32_t last_action_ms;
    uint32_t variable_interval_ms;
    uint8_t* memory_stress_ptr;
    size_t   memory_stress_size;
    
    // Safe socket transaction helper
    void performSocketExchange(uint16_t payloadBytes);
    void performSafeComputation(uint32_t targetTimeMs);
};

extern TrafficGenerator TrafficGen;

#endif // TRAFFIC_GENERATOR_H
