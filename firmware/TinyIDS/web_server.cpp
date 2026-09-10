#include "web_server.h"

WebDashboard Dashboard;

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TinyIDS — On-Device Security Dashboard</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-primary: #c9d1d9;
            --text-muted: #8b949e;
            --accent-green: #2ea043;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --accent-blue: #58a6ff;
            --accent-purple: #bc8cff;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
        body { background-color: var(--bg-color); color: var(--text-primary); padding: 20px; max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; border-bottom: 1px solid var(--border-color); margin-bottom: 20px; }
        h1 { font-size: 1.4rem; color: var(--accent-blue); display: flex; align-items: center; gap: 10px; }
        .badge-mode { background: #21262d; border: 1px solid var(--border-color); padding: 4px 10px; borderRadius: 6px; font-size: 0.8rem; color: var(--text-muted); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; }
        .card-header { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 10px; display: flex; justify-content: space-between; }
        
        /* Status Banner */
        .status-banner { border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px; transition: all 0.3s ease; }
        .status-normal { background: rgba(46, 160, 67, 0.15); border: 2px solid var(--accent-green); color: var(--accent-green); }
        .status-anomaly { background: rgba(248, 81, 73, 0.2); border: 2px solid var(--accent-red); color: var(--accent-red); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 0.9; } 50% { opacity: 1; box-shadow: 0 0 15px rgba(248, 81, 73, 0.4); } 100% { opacity: 0.9; } }
        .status-title { font-size: 1.8rem; font-weight: bold; margin-bottom: 5px; }
        .status-sub { font-size: 0.9rem; opacity: 0.85; }

        /* Risk Gauge */
        .meter-container { background: #21262d; border-radius: 10px; height: 16px; overflow: hidden; margin-top: 10px; border: 1px solid var(--border-color); }
        .meter-fill { height: 100%; width: 0%; transition: width 0.5s ease, background 0.5s ease; }

        /* Metric Rows */
        .metric-val { font-size: 1.5rem; font-weight: 600; color: #f0f6fc; }
        .metric-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

        /* Indicators list */
        .indicator-tag { display: inline-block; background: #21262d; border: 1px solid var(--border-color); border-radius: 4px; padding: 4px 8px; font-size: 0.8rem; margin: 3px; color: var(--accent-yellow); }
        .path-box { font-family: monospace; background: #0d1117; padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); font-size: 0.8rem; color: var(--accent-purple); overflow-x: auto; white-space: pre-wrap; }

        /* Chart Canvas */
        canvas { width: 100%; height: 150px; background: #0d1117; border-radius: 6px; border: 1px solid var(--border-color); }
    </style>
</head>
<body>

    <header>
        <h1>🛡️ TinyIDS — Arduino Nano ESP32</h1>
        <div class="badge-mode" id="wifi-badge">Wi-Fi: Connecting...</div>
    </header>

    <!-- Main Status Banner -->
    <div id="status-banner" class="status-banner status-normal">
        <div class="status-title" id="status-text">INITIALIZING...</div>
        <div class="status-sub" id="status-sub">Listening to physical ESP32-S3 telemetry windows</div>
    </div>

    <!-- Security & ML Overview Grid -->
    <div class="grid">
        <div class="card">
            <div class="card-header"><span>Behavioral Risk Score</span> <span id="severity-badge">LOW</span></div>
            <div class="metric-val" id="risk-val">0 / 100</div>
            <div class="meter-container">
                <div class="meter-fill" id="meter-bar"></div>
            </div>
            <div class="metric-sub" id="risk-sub">Evaluated by on-device decision tree</div>
        </div>

        <div class="card">
            <div class="card-header"><span>ML Decision Engine</span> <span>DecisionTree</span></div>
            <div class="metric-val" id="ml-pred">NORMAL</div>
            <div class="metric-sub" id="ml-sub">Confidence: --% | Latency: -- µs</div>
            <div class="metric-sub" style="margin-top:4px;" id="ml-consensus">Temporal Consensus: NORMAL</div>
        </div>

        <div class="card">
            <div class="card-header"><span>System Memory</span> <span>SRAM</span></div>
            <div class="metric-val" id="heap-val">-- B</div>
            <div class="metric-sub" id="heap-sub">Delta: 0 B | Min: -- B</div>
        </div>
    </div>

    <!-- Behavioral Explanations & Decision Path -->
    <div class="grid">
        <div class="card">
            <div class="card-header"><span>Behavioral Indicators</span></div>
            <div id="indicators-list">
                <span class="indicator-tag">✔ Normal baseline operation</span>
            </div>
        </div>
        <div class="card">
            <div class="card-header"><span>Decision Path</span></div>
            <div class="path-box" id="path-text">x[loop_jitter_ms] <= -0.852 → NORMAL_BASELINE</div>
        </div>
    </div>

    <!-- Live Telemetry Matrix -->
    <div class="card" style="margin-bottom:20px;">
        <div class="card-header"><span>Real-Time Hardware Telemetry (10 Features)</span> <span id="win-id">Window #--</span></div>
        <div class="grid" style="margin-bottom:0; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
            <div><div class="metric-sub">Transaction Rate</div><div class="metric-val" style="font-size:1.1rem;" id="f-tx-rate">0 ops/s</div></div>
            <div><div class="metric-sub">Byte Throughput</div><div class="metric-val" style="font-size:1.1rem;" id="f-byte-rate">0 B/s</div></div>
            <div><div class="metric-sub">Free Heap</div><div class="metric-val" style="font-size:1.1rem;" id="f-free-heap">0 B</div></div>
            <div><div class="metric-sub">Heap Delta</div><div class="metric-val" style="font-size:1.1rem;" id="f-heap-delta">0 B</div></div>
            <div><div class="metric-sub">Loop Avg Latency</div><div class="metric-val" style="font-size:1.1rem;" id="f-loop-avg">0.00 ms</div></div>
            <div><div class="metric-sub">Loop Max Latency</div><div class="metric-val" style="font-size:1.1rem;" id="f-loop-max">0.00 ms</div></div>
            <div><div class="metric-sub">Loop Jitter</div><div class="metric-val" style="font-size:1.1rem;" id="f-loop-jitter">0.00 ms</div></div>
            <div><div class="metric-sub">Wi-Fi Signal (RSSI)</div><div class="metric-val" style="font-size:1.1rem;" id="f-rssi">-127 dBm</div></div>
            <div><div class="metric-sub">Inter-Arrival Time</div><div class="metric-val" style="font-size:1.1rem;" id="f-iat">0.00 ms</div></div>
            <div><div class="metric-sub">Socket Errors</div><div class="metric-val" style="font-size:1.1rem;" id="f-errors">0</div></div>
        </div>
    </div>

    <!-- Risk Score Timeline Chart -->
    <div class="card">
        <div class="card-header"><span>Behavioral Risk History (Last 20 Windows)</span></div>
        <canvas id="risk-chart"></canvas>
    </div>

    <script>
        const historyData = [];

        function updateUI(data) {
            const isAnomaly = (data.prediction === 1);
            const banner = document.getElementById('status-banner');
            const statusText = document.getElementById('status-text');
            const statusSub = document.getElementById('status-sub');

            if (isAnomaly) {
                banner.className = "status-banner status-anomaly";
                statusText.innerText = "⚠️ ANOMALY DETECTED";
                statusSub.innerText = "Behavioral anomaly flagged by TinyML Decision Tree";
            } else {
                banner.className = "status-banner status-normal";
                statusText.innerText = "SYSTEM NORMAL";
                statusSub.innerText = "On-device telemetry within trained baseline limits";
            }

            // Wi-Fi badge
            document.getElementById('wifi-badge').innerText = `Wi-Fi: ${data.wifi_mode} (${data.ip})`;

            // Risk Meter
            const risk = data.risk_score || 0;
            document.getElementById('risk-val').innerText = `${risk} / 100`;
            document.getElementById('severity-badge').innerText = data.severity || "LOW";
            const bar = document.getElementById('meter-bar');
            bar.style.width = `${risk}%`;
            bar.style.background = risk >= 80 ? 'var(--accent-red)' : (risk >= 50 ? 'var(--accent-yellow)' : 'var(--accent-green)');

            // ML Decision
            document.getElementById('ml-pred').innerText = isAnomaly ? "ANOMALY" : "NORMAL";
            document.getElementById('ml-pred').style.color = isAnomaly ? "var(--accent-red)" : "var(--accent-green)";
            document.getElementById('ml-sub').innerText = `Confidence: ${(data.confidence * 100).toFixed(1)}% | Latency: ${data.inference_time_us} µs`;
            document.getElementById('ml-consensus').innerText = `Temporal Consensus: ${data.smoothed_prediction === 1 ? "ANOMALY" : "NORMAL"}`;

            // Memory
            document.getElementById('heap-val').innerText = `${data.free_heap.toLocaleString()} B`;
            document.getElementById('heap-sub').innerText = `Delta: ${data.heap_delta} B | Scenario: ${data.scenario}`;

            // Telemetry Features
            document.getElementById('win-id').innerText = `Window #${data.window_id}`;
            document.getElementById('f-tx-rate').innerText = `${data.transaction_rate.toFixed(2)} ops/s`;
            document.getElementById('f-byte-rate').innerText = `${data.byte_rate.toFixed(1)} B/s`;
            document.getElementById('f-free-heap').innerText = `${data.free_heap.toLocaleString()} B`;
            document.getElementById('f-heap-delta').innerText = `${data.heap_delta} B`;
            document.getElementById('f-loop-avg').innerText = `${data.loop_avg_ms.toFixed(3)} ms`;
            document.getElementById('f-loop-max').innerText = `${data.loop_max_ms.toFixed(3)} ms`;
            document.getElementById('f-loop-jitter').innerText = `${data.loop_jitter_ms.toFixed(3)} ms`;
            document.getElementById('f-rssi').innerText = data.wifi_rssi === -127 ? "OFFLINE (-127)" : `${data.wifi_rssi} dBm`;
            document.getElementById('f-iat').innerText = `${data.avg_inter_arrival_ms.toFixed(1)} ms`;
            document.getElementById('f-errors').innerText = `${data.socket_errors}`;

            // Behavioral Indicators
            const indList = document.getElementById('indicators-list');
            indList.innerHTML = '';
            const reason = data.primary_reason || "NORMAL_BASELINE";
            if (reason.includes("ANOMALY") || isAnomaly) {
                const tag = document.createElement('span');
                tag.className = 'indicator-tag';
                tag.style.borderColor = 'var(--accent-red)';
                tag.style.color = 'var(--accent-red)';
                tag.innerText = `🚨 ${reason.replace('ANOMALY_', '')}`;
                indList.appendChild(tag);

                if (data.transaction_rate > 10) {
                    const t = document.createElement('span'); t.className='indicator-tag'; t.innerText='↑ High Transaction Rate'; indList.appendChild(t);
                }
                if (data.loop_max_ms > 10) {
                    const t = document.createElement('span'); t.className='indicator-tag'; t.innerText='↑ CPU Loop Latency Spike'; indList.appendChild(t);
                }
                if (data.heap_delta < -10000) {
                    const t = document.createElement('span'); t.className='indicator-tag'; t.innerText='↓ Rapid Heap Allocation'; indList.appendChild(t);
                }
                if (data.socket_errors > 0) {
                    const t = document.createElement('span'); t.className='indicator-tag'; t.innerText='↑ Socket Connection Failures'; indList.appendChild(t);
                }
            } else {
                indList.innerHTML = '<span class="indicator-tag" style="color:var(--accent-green); border-color:var(--accent-green);">✔ Baseline Operating Parameters</span>';
            }

            // Path Text
            document.getElementById('path-text').innerText = `Feature Decision Indicator: ${reason}\nPrimary Trigger: ${data.primary_reason}`;

            // Add to history for chart
            historyData.push({ win: data.window_id, risk: risk, isAnomaly: isAnomaly });
            if (historyData.length > 20) historyData.shift();
            drawChart();
        }

        function drawChart() {
            const canvas = document.getElementById('risk-chart');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.parentElement.clientWidth - 32;
            canvas.height = 150;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (historyData.length < 2) return;

            const margin = 30;
            const w = canvas.width - margin * 2;
            const h = canvas.height - margin * 2;

            // Draw Threshold Line at Risk = 60
            const threshY = canvas.height - margin - (60 / 100 * h);
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(248, 81, 73, 0.4)';
            ctx.setLineDash([4, 4]);
            ctx.moveTo(margin, threshY);
            ctx.lineTo(canvas.width - margin, threshY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw Risk Line
            ctx.beginPath();
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#58a6ff';

            const step = w / (historyData.length - 1);
            historyData.forEach((d, i) => {
                const x = margin + i * step;
                const y = canvas.height - margin - (d.risk / 100 * h);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // Draw Points
            historyData.forEach((d, i) => {
                const x = margin + i * step;
                const y = canvas.height - margin - (d.risk / 100 * h);
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fillStyle = d.isAnomaly ? '#f85149' : '#2ea043';
                ctx.fill();
            });
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                if (res.ok) {
                    const data = await res.json();
                    updateUI(data);
                }
            } catch (e) {
                console.log('Fetch status error:', e);
            }
        }

        setInterval(fetchStatus, 1500);
        fetchStatus();
    </script>
</body>
</html>
)rawliteral";

WebDashboard::WebDashboard() {
    in_softap_mode = false;
    history_head = 0;
    history_count = 0;
    for (int i = 0; i < HISTORY_SIZE; i++) {
        history[i].valid = false;
    }
}

void WebDashboard::begin() {
    if (WiFi.status() == WL_CONNECTED) {
        in_softap_mode = false;
        ip_address = WiFi.localIP();
        Serial.printf("\n[WEB SERVER] Running in STA mode at http://%s/\n", ip_address.toString().c_str());
    } else {
        in_softap_mode = true;
        WiFi.mode(WIFI_AP_STA);
        WiFi.softAP(SOFTAP_SSID_DEFAULT, SOFTAP_PASSWORD_DEFAULT);
        ip_address = WiFi.softAPIP();
        Serial.println("\n[WEB SERVER] Running in SoftAP mode:");
        Serial.printf("  SSID: %s\n", SOFTAP_SSID_DEFAULT);
        Serial.printf("  Dashboard URL: http://%s/\n\n", ip_address.toString().c_str());
    }

    setupRoutes();
    server.begin();
}

void WebDashboard::setupRoutes() {
    server.on("/", HTTP_GET, [this]() { handleRoot(); });
    server.on("/api/status", HTTP_GET, [this]() { handleApiStatus(); });
    server.on("/api/history", HTTP_GET, [this]() { handleApiHistory(); });
}

void WebDashboard::handleRoot() {
    server.send(200, "text/html", INDEX_HTML);
}

void WebDashboard::handleApiStatus() {
    if (history_count == 0) {
        server.send(200, "application/json", "{\"status\":\"NO_DATA\"}");
        return;
    }

    uint8_t latest_idx = (history_head == 0) ? (HISTORY_SIZE - 1) : (history_head - 1);
    HistoryEntry entry = history[latest_idx];

    char buf[768];
    snprintf(buf, sizeof(buf),
        "{"
        "\"timestamp_ms\":%u,"
        "\"window_id\":%u,"
        "\"scenario\":\"%s\","
        "\"label\":%u,"
        "\"transaction_rate\":%.2f,"
        "\"byte_rate\":%.1f,"
        "\"free_heap\":%u,"
        "\"heap_delta\":%d,"
        "\"loop_avg_ms\":%.4f,"
        "\"loop_max_ms\":%.4f,"
        "\"loop_jitter_ms\":%.4f,"
        "\"wifi_rssi\":%d,"
        "\"avg_inter_arrival_ms\":%.2f,"
        "\"socket_errors\":%u,"
        "\"prediction\":%u,"
        "\"confidence\":%.4f,"
        "\"risk_score\":%u,"
        "\"severity\":\"%s\","
        "\"primary_reason\":\"%s\","
        "\"smoothed_prediction\":%u,"
        "\"inference_time_us\":%u,"
        "\"wifi_mode\":\"%s\","
        "\"ip\":\"%s\""
        "}",
        entry.window.timestamp_ms,
        entry.window.window_id,
        getScenarioName(entry.window.scenario_id),
        entry.window.label,
        entry.window.transaction_rate,
        entry.window.byte_rate,
        entry.window.free_heap,
        entry.window.heap_delta,
        entry.window.loop_avg_ms,
        entry.window.loop_max_ms,
        entry.window.loop_jitter_ms,
        entry.window.wifi_rssi,
        entry.window.avg_inter_arrival_ms,
        entry.window.socket_errors,
        entry.result.prediction,
        entry.result.confidence,
        entry.result.risk_score,
        entry.result.severity,
        entry.result.primary_reason,
        entry.result.smoothed_prediction,
        entry.result.inference_time_us,
        in_softap_mode ? "SoftAP" : "Station",
        ip_address.toString().c_str()
    );

    server.send(200, "application/json", buf);
}

void WebDashboard::handleApiHistory() {
    String json = "[";
    uint8_t count = 0;
    for (uint8_t i = 0; i < history_count; i++) {
        uint8_t idx = (history_head + HISTORY_SIZE - history_count + i) % HISTORY_SIZE;
        if (!history[idx].valid) continue;
        if (count > 0) json += ",";
        char buf[128];
        snprintf(buf, sizeof(buf), "{\"win\":%u,\"risk\":%u,\"pred\":%u}",
            history[idx].window.window_id,
            history[idx].result.risk_score,
            history[idx].result.prediction
        );
        json += buf;
        count++;
    }
    json += "]";
    server.send(200, "application/json", json);
}

void WebDashboard::handleClient() {
    server.handleClient();
}

void WebDashboard::pushResult(const TelemetryWindow& win, const InferenceResult& res) {
    history[history_head].window = win;
    history[history_head].result = res;
    history[history_head].valid = true;

    history_head = (history_head + 1) % HISTORY_SIZE;
    if (history_count < HISTORY_SIZE) history_count++;
}
