import json
import re

def extract_json(text: str):
    try:
        return json.loads(text)
    except:
        pass

    # extract JSON block from ```json
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    raise ValueError("No valid JSON found")