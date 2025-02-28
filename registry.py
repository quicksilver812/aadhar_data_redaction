import json
CONFIG_FILE = "aadhaar_config.json"

def get_processed_count():
    """Read processed count from JSON config"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('processed_count', 0)
    except FileNotFoundError:
        return 0

def update_processed_count(new_count):
    """Update processed count in JSON config"""
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        pass
    
    config['processed_count'] = new_count
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
