"""Application configuration module.

This module loads and manages application configuration including:
- Tapo device credentials from environment variables
- Storage file paths for schedules, config, and activity logs
- Plug IP address mappings
- Rate limiting settings
"""

import os

# Configuration from environment variables
TAPO_USERNAME = os.getenv("TAPO_USERNAME")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")
TAPO_IP_1 = os.getenv("TAPO_IP_1")
TAPO_IP_2 = os.getenv("TAPO_IP_2")

# Storage files
SCHEDULE_FILE = "data/schedules.json"
CONFIG_FILE = "data/config.json"
ACTIVITY_LOG_FILE = "data/activity_log.json"

# Plug IPs mapping
PLUG_IPS = {
    "1": TAPO_IP_1,
    "2": TAPO_IP_2
}

# Rate limiting
REQUEST_COOLDOWN = 0.5  # seconds between requests to same plug

# Print configuration on startup
print("Starting Tapo Control App")
print(f"Username: {TAPO_USERNAME}")
print(f"IP 1: {TAPO_IP_1}")
print(f"IP 2: {TAPO_IP_2}")
print(f"Password: {'*' * len(TAPO_PASSWORD) if TAPO_PASSWORD else 'NOT SET'}")
