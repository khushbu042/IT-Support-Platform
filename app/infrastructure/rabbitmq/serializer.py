from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dumps(payload: BaseModel) -> bytes:
    return payload.model_dump_json().encode("utf-8")


def loads(body: bytes, model: type[T]) -> T:
    return model.model_validate_json(body)
