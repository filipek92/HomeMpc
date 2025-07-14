import os

PORT = int(os.environ.get("PORT", "26781"))
DATA_DIR = os.environ.get("HA_ADDON_DATA", "./data")
OPTIONS_FILE = os.path.join(DATA_DIR, "options.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "credentials.yaml")
SETTINGS_FILE = os.path.join(DATA_DIR, "powerplan_settings.json")

HA_ADDON = os.environ.get("HA_ADDON")

RESULTS_DIR = os.path.join(DATA_DIR, "results")
LATEST_LINK = os.path.join(RESULTS_DIR, "latest.json")
LATEST_CSV = os.path.join(RESULTS_DIR, "latest.csv")
# Ensure results directory exists on startup
os.makedirs(RESULTS_DIR, exist_ok=True)