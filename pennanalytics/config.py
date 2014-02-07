from yaml import safe_load

with open('config.yaml', 'r') as f:
    hosts = safe_load(f)
