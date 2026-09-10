#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "telemetry.h"
#include "traffic_generator.h"
#include "scenario_manager.h"
#include "serial_logger.h"
#include "inference.h"
#include "web_server.h"

// Enforce exact memory footprint: 76 bytes per window
static_assert(sizeof(TelemetryWindow) == 76,
              "TelemetryWindow struct size must be exactly 76 bytes.");

uint32_t current_window_id = 1;
String serial_cmd_buffer = "";

void processSerialCommand(String cmd) {
    cmd.trim();
    cmd.toUpperCase();
    if (cmd.length() == 0) return;
    
    if (cmd == "HELP") {
        Logger.printHelp();
    } else if (cmd == "STATUS") {
        Serial.printf("\n[STATUS] Uptime: %u ms | Free Heap: %u B | WiFi: %s | Active Scenario: %s\n\n",
                      millis(), ESP.getFreeHeap(), WiFi.status() == WL_CONNECTED ? "CONNECTED" : "OFFLINE",
                      getScenarioName(ScenarioMgr.getActiveScenario()));
    } else if (cmd == "DASHBOARD") {
        Logger.setMode(MODE_DASHBOARD);
    } else if (cmd == "CSV") {
        Logger.setMode(MODE_CSV);
    } else if (cmd == "IDLE" || cmd == "NORMAL_IDLE") {
        ScenarioMgr.setScenario(SCENARIO_NORMAL_IDLE);
        Serial.println("[CMD] Scenario switched to SCENARIO_NORMAL_IDLE");
    } else if (cmd == "PERIODIC" || cmd == "NORMAL" || cmd == "NORMAL_PERIODIC") {
        ScenarioMgr.setScenario(SCENARIO_NORMAL_PERIODIC);
        Serial.println("[CMD] Scenario switched to SCENARIO_NORMAL_PERIODIC");
    } else if (cmd == "VARIABLE" || cmd == "NORMAL_VARIABLE") {
        ScenarioMgr.setScenario(SCENARIO_NORMAL_VARIABLE);
        Serial.println("[CMD] Scenario switched to SCENARIO_NORMAL_VARIABLE");
    } else if (cmd == "HIGH_RATE" || cmd == "ANOMALY_HIGH_RATE") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_HIGH_RATE);
        Serial.println("[CMD] Scenario switched to ANOMALY_HIGH_RATE (Traffic Flood)");
    } else if (cmd == "BURST" || cmd == "ANOMALY_BURST") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_BURST);
        Serial.println("[CMD] Scenario switched to ANOMALY_BURST (Rapid Bursts)");
    } else if (cmd == "CONNECTION" || cmd == "ANOMALY_CONNECTION_STRESS") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_CONNECTION_STRESS);
        Serial.println("[CMD] Scenario switched to ANOMALY_CONNECTION_STRESS");
    } else if (cmd == "COMPUTE" || cmd == "ANOMALY_COMPUTE") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_COMPUTE);
        Serial.println("[CMD] Scenario switched to ANOMALY_COMPUTE (CPU Starvation)");
    } else if (cmd == "MEMORY" || cmd == "ANOMALY_MEMORY") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_MEMORY);
        Serial.println("[CMD] Scenario switched to ANOMALY_MEMORY (Allocation Pressure)");
    } else if (cmd == "COMBINED" || cmd == "ANOMALY_COMBINED") {
        ScenarioMgr.setScenario(SCENARIO_ANOMALY_COMBINED);
        Serial.println("[CMD] Scenario switched to ANOMALY_COMBINED (Traffic + Compute)");
    } else {
        Serial.printf("[WARN] Unknown command '%s'. Type 'HELP' for valid commands.\n", cmd.c_str());
    }
}

void setup() {
    Logger.begin();
    
#if HAS_WIFI_CONFIG == 1
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID_DEFAULT, WIFI_PASSWORD_DEFAULT);
    uint32_t wifi_start = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - wifi_start < 4000)) {
        delay(100);
    }
#else
    // Offline mode: do not attempt connection if credentials not configured
    WiFi.mode(WIFI_OFF);
#endif
    
    Telemetry.begin();
    TrafficGen.begin();
    ScenarioMgr.begin();
    TinyML.begin();
    Dashboard.begin();
    
    // Default safe initial state: NORMAL_PERIODIC
    ScenarioMgr.setScenario(SCENARIO_NORMAL_PERIODIC);
    Telemetry.startWindow(current_window_id, ScenarioMgr.getActiveScenario(), ScenarioMgr.getActiveLabel());
}

void loop() {
    // Service HTTP requests for live security dashboard
    Dashboard.handleClient();

    // Check for interactive user commands over Serial CLI
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_cmd_buffer.length() > 0) {
                processSerialCommand(serial_cmd_buffer);
                serial_cmd_buffer = "";
            }
        } else {
            serial_cmd_buffer += c;
        }
    }
    
    // 1. Measure Loop Execution Start
    Telemetry.recordLoopStart();
    
    // 2. Execute Workload corresponding to Active Scenario
    uint8_t scenario = ScenarioMgr.getActiveScenario();
    switch (scenario) {
        case SCENARIO_NORMAL_IDLE:
            TrafficGen.executeIdle();
            break;
        case SCENARIO_NORMAL_PERIODIC:
            TrafficGen.executeNormalPeriodic();
            break;
        case SCENARIO_NORMAL_VARIABLE:
            TrafficGen.executeNormalVariable();
            break;
        case SCENARIO_ANOMALY_HIGH_RATE:
            TrafficGen.executeAnomalyHighRate();
            break;
        case SCENARIO_ANOMALY_BURST:
            TrafficGen.executeAnomalyBurst();
            break;
        case SCENARIO_ANOMALY_CONNECTION_STRESS:
            TrafficGen.executeAnomalyConnectionStress();
            break;
        case SCENARIO_ANOMALY_COMPUTE:
            TrafficGen.executeAnomalyCompute();
            break;
        case SCENARIO_ANOMALY_MEMORY:
            TrafficGen.executeAnomalyMemory();
            break;
        case SCENARIO_ANOMALY_COMBINED:
            TrafficGen.executeAnomalyCombined();
            break;
        default:
            TrafficGen.executeIdle();
            break;
    }
    
    // 3. Record Loop Execution End
    Telemetry.recordLoopEnd();
    
    // 4. Check if 5000 ms Window is Complete
    if (Telemetry.isWindowComplete()) {
        TelemetryWindow win = Telemetry.closeWindow();
        InferenceResult ml = TinyML.predict(win);
        Logger.logWindow(win, ml);
        Dashboard.pushResult(win, ml);
        
        ScenarioMgr.advanceScenario();
        current_window_id++;
        Telemetry.startWindow(current_window_id, ScenarioMgr.getActiveScenario(), ScenarioMgr.getActiveLabel());
    }
}
