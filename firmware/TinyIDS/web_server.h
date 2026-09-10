#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>
#include "config.h"
#include "telemetry.h"
#include "inference.h"

struct HistoryEntry {
    TelemetryWindow window;
    InferenceResult result;
    bool valid;
};

class WebDashboard {
public:
    WebDashboard();
    void begin();
    void handleClient();
    void pushResult(const TelemetryWindow& win, const InferenceResult& res);

    bool isSoftAP() const { return in_softap_mode; }
    IPAddress getIP() const { return ip_address; }

private:
    WebServer server;
    bool in_softap_mode;
    IPAddress ip_address;

    static const uint8_t HISTORY_SIZE = 20;
    HistoryEntry history[HISTORY_SIZE];
    uint8_t history_head;
    uint8_t history_count;

    void setupRoutes();
    void handleRoot();
    void handleApiStatus();
    void handleApiHistory();
};

extern WebDashboard Dashboard;

#endif // WEB_SERVER_H
