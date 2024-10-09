import json
from typing import Dict, List


def save_to_json(data: List[Dict], filename: str) -> None:
    """Save a list of dictionaries to a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
