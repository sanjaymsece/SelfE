import json


def as_json_block(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
