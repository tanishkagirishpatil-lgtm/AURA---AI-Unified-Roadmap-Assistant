import json
from json_repair import repair_json
import ast


def extract_json_safe(text: str):

    if not text:
        raise ValueError("Empty response")

    text = text.replace("```json", "")
    text = text.replace("```", "")

    repaired = repair_json(text)

    return json.loads(repaired)


import ast

def safe_validate(model, data):

    try:
        return model(**data)

    except Exception:

        fixed = {}

        for field_name, field_info in model.model_fields.items():

            value = data.get(field_name)

            if value is None:
                continue

            annotation = str(field_info.annotation)

            try:

                if isinstance(value, str):

                    if "dict" in annotation:
                        value = ast.literal_eval(value)

                    elif "list" in annotation:
                        value = ast.literal_eval(value)

                    elif "float" in annotation:
                        value = float(value)

                    elif "int" in annotation:
                        value = int(value)

                fixed[field_name] = value

            except:
                fixed[field_name] = value

        return model(**fixed)