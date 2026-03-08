import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    else:
        # Fallback defaults if config missing
        return {
            "log_file": "logs/auth.log",
            "threat_thresholds": {"critical": 10, "high": 6, "medium": 3},
            "enable_geolocation": True,
            "enable_threat_intel": True
        }

CONFIG = load_config()
