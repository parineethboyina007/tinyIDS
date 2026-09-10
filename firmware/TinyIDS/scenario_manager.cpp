#include "scenario_manager.h"

ScenarioManager ScenarioMgr;

ScenarioManager::ScenarioManager() {
    current_scenario = SCENARIO_NORMAL_IDLE;
    target_windows = DEFAULT_SCENARIO_WINDOWS;
    windows_in_scenario = 0;
    is_transition_window = false;
}

void ScenarioManager::begin() {
    current_scenario = SCENARIO_NORMAL_IDLE;
    windows_in_scenario = 0;
    is_transition_window = false;
}

uint8_t ScenarioManager::getActiveLabel() const {
    if (is_transition_window) {
        return LABEL_TRANSITION; // Discard mixed window from ML
    }
    
    // Normal scenarios
    if (current_scenario == SCENARIO_NORMAL_IDLE ||
        current_scenario == SCENARIO_NORMAL_PERIODIC ||
        current_scenario == SCENARIO_NORMAL_VARIABLE) {
        return LABEL_NORMAL;
    }
    // Anomaly scenarios
    return LABEL_ANOMALY;
}

void ScenarioManager::setScenario(uint8_t scenarioId, uint32_t durationWindows) {
    if (scenarioId < SCENARIO_COUNT) {
        current_scenario = scenarioId;
        target_windows = durationWindows;
        windows_in_scenario = 0;
        is_transition_window = true; // Mark next window as transition
    }
}

void ScenarioManager::advanceScenario() {
    windows_in_scenario++;
    if (is_transition_window) {
        // First window after switch was discarded as transition; now enter steady state
        is_transition_window = false;
    }
    
    // Automatically cycle through scenarios for automated dataset generation
    if (windows_in_scenario >= target_windows) {
        uint8_t next = (current_scenario + 1) % SCENARIO_COUNT;
        setScenario(next, DEFAULT_SCENARIO_WINDOWS);
    }
}

void ScenarioManager::update() {
    // Active periodic scenario checks
}
