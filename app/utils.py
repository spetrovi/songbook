import json

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError


def valid_schema_data_or_error(raw_data: dict, SchemaModel: BaseModel):
    data = {}
    errors = []
    error_str = None
    try:
        cleaned_data = SchemaModel(**raw_data)
        data = cleaned_data.dict()
    except ValidationError as e:
        error_str = e.json()
    if error_str is not None:
        try:
            errors = json.loads(error_str)
        except Exception:
            errors = [{"loc": "non_field_error", "msg": "Unknown error"}]
    return data, errors
