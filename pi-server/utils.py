from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Union


def to_camel_case(snake_str):
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def to_json(obj: Union[dataclass, list[dataclass]]) -> bytes:
    def convert_to_camel_case_with_enum_handling(obj):
        if isinstance(obj, list):
            return [convert_to_camel_case_with_enum_handling(item) for item in obj]
        if isinstance(obj, dict):
            return {
                to_camel_case(k): convert_to_camel_case_with_enum_handling(v)
                for k, v in obj.items()
            }
        if isinstance(obj, Enum):
            return to_camel_case(
                obj.value
            )  # Take only the value of the enum and convert to camel case
        return obj

    if isinstance(obj, list):
        json_str = json.dumps(
            [convert_to_camel_case_with_enum_handling(asdict(item)) for item in obj],
            indent=2,
        )
    else:
        json_str = json.dumps(
            convert_to_camel_case_with_enum_handling(asdict(obj)), indent=2
        )

    return json_str.encode("utf-8")
