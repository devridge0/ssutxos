import json
from pathlib import Path

def load_json(path):
    p = Path(path)
    return json.loads(p.read_text())

def save_json(obj, path):
    p = Path(path)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))
    