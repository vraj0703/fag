import os

import yaml

# Load the YAML config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

print(config["allowed_extensions"])
print(config["logging"]["dir"])
