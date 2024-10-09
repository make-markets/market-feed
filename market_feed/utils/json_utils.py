import json
import os
from typing import Any, List


def load_from_json(file_path: str) -> List[Any]:
    """Load a list of dictionaries from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []


def save_to_json(data: List[Any], file_path: str) -> None:
    """Save a list of dictionaries to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def append_to_json(item: Any, file_path: str) -> None:
    """Append an item to a JSON file."""
    existing_data = load_from_json(file_path)
    existing_data.append(item)
    save_to_json(existing_data, file_path)
