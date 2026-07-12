import json
import os

def save_output(data, filename="idea_output.json"):
    os.makedirs("outputs", exist_ok=True)

    path = os.path.join("outputs", filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"\nSaved at: {path}")