import json
import os

# Default values
MASTER_VOLUME = 0.75
SFX_VOLUME = 0.5

CONFIG_PATH = "config.json"

def load_config():
    global MASTER_VOLUME, SFX_VOLUME
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                MASTER_VOLUME = config.get("master_vol", MASTER_VOLUME)
                SFX_VOLUME = config.get("sfx_vol", SFX_VOLUME)
        except Exception as e:
            print(f"Error loading config: {e}")

# Load on import
load_config()
