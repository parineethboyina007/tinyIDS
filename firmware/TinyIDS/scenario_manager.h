#ifndef SCENARIO_MANAGER_H
#define SCENARIO_MANAGER_H

#include <Arduino.h>
#include "config.h"

class ScenarioManager {
public:
    ScenarioManager();
    void begin();
    void update();
    
    uint8_t getActiveScenario() const { return current_scenario; }
    uint8_t getActiveLabel() const;
    uint32_t getWindowCountInScenario() const { return windows_in_scenario; }
    
    void setScenario(uint8_t scenarioId, uint32_t durationWindows = DEFAULT_SCENARIO_WINDOWS);
    void advanceScenario();

private:
    uint8_t  current_scenario;
    uint32_t target_windows;
    uint32_t windows_in_scenario;
    bool     is_transition_window;
};

extern ScenarioManager ScenarioMgr;

#endif // SCENARIO_MANAGER_H
