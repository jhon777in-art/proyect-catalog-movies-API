from collections.abc import Mapping, Sequence
from typing import Any

from bson import ObjectId


def is_valid_object_id(value: str) -> bool:
    return ObjectId.is_valid(value)


def object_id_to_string(value: ObjectId | str) -> str:
    return str(value)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Mapping):
        return serialize_mongo_document(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def serialize_mongo_document(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in document.items()}


def serialize_mongo_documents(
    documents: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [serialize_mongo_document(document) for document in documents]