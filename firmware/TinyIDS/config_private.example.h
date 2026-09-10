#ifndef CONFIG_PRIVATE_H
#define CONFIG_PRIVATE_H

// ==============================================================================
// TinyIDS Private Configuration Template
// Copy this file to config_private.h and fill in your local Wi-Fi credentials.
// config_private.h is gitignored to prevent accidental credential leakage.
// ==============================================================================

#define WIFI_SSID_DEFAULT     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD_DEFAULT "YOUR_WIFI_PASSWORD"

// Optional test local echo/HTTP target (e.g., local router or host computer)
#define TEST_SERVER_HOST      "192.168.1.1"
#define TEST_SERVER_PORT      80

#endif // CONFIG_PRIVATE_H
