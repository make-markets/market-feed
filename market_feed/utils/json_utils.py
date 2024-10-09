import json
from typing import Dict, List


def save_to_json(data: List[Dict], filename: str) -> None:
    """Save a list of dictionaries to a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_from_json(filename: str) -> List[Dict]:
    """Load a list of dictionaries from a JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
