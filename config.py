import yaml

# Load the YAML config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

print(config["allowed_extensions"])
print(config["logging"]["dir"])
