#ifndef SERIAL_LOGGER_H
#define SERIAL_LOGGER_H

#include <Arduino.h>
#include "telemetry.h"
#include "inference.h"

class SerialLogger {
public:
    SerialLogger();
    void begin();
    void setMode(uint8_t mode);
    uint8_t getMode() const { return current_mode; }
    
    void printBootBanner();
    void printHelp();
    void printCsvHeader();
    void logWindow(const TelemetryWindow& win, const InferenceResult& ml);

private:
    uint8_t current_mode;
    bool    header_printed;
};

extern SerialLogger Logger;

#endif // SERIAL_LOGGER_H
