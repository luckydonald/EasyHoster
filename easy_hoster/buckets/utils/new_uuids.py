from pydantic import BaseModel, PlainValidator, GetPydanticSchema
from dataclasses import dataclass
from typing import Annotated, Any, Literal, ClassVar

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, UUID3
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticCustomError, core_schema
from uuid6 import UUID
import uuid6
import uuid


@dataclass(slots=True)
class UuidVersion:
    """A field metadata class to indicate a [UUID](https://pypi.org/project/uuid6/) version."""
    # Based on https://github.com/pydantic/pydantic/discussions/10305#discussioncomment-10590583

    uuid_version: ClassVar[Literal[6, 7, 8]]

    def __class_getitem__(cls, version: Literal[6, 7, 8]):
        return type(f"UuidVersion{version}", (cls,), {"uuid_version": version})
    # end def

    def __get_pydantic_json_schema__(
        self,
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.pop("anyOf", None)  # remove the bytes/str union
        field_schema.update(type="string", format=f"uuid{self.uuid_version}")
        return field_schema
    # end def

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls._validate_uuid,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(UUID),
                    core_schema.int_schema(),
                    core_schema.bytes_schema(),
                    core_schema.str_schema(),
                ],
            ),
        )
    # end def

    @classmethod
    def _validate_uuid(
        cls,
        value: Any,
        handler: core_schema.ValidatorFunctionWrapHandler,
    ) -> UUID:
        uuid: UUID
        try:
            if isinstance(value, int):
                uuid = UUID(int=value)
            elif isinstance(value, str):
                uuid = UUID(value)
            elif isinstance(value, bytes):
                uuid = UUID(bytes=value)
            elif isinstance(value, UUID):
                uuid = value
            else:
                raise ValueError("Unrecognized format")
            # end if
        except ValueError as e:
            raise PydanticCustomError("uuid_format", "Unrecognized format")  # noqa: B904
        # end try

        if uuid.version != cls.uuid_version:
            raise PydanticCustomError("uuid_version", "Invalid UUID version")
        # end if

        return handler(uuid)
    # end def

    def __hash__(self) -> int:
        return hash(type(self.uuid_version))
    # end def
# end class


UUID6 = Annotated[UUID, UuidVersion[6]]
UUID7_1 = Annotated[UUID, UuidVersion[7]]
UUID8 = Annotated[UUID, UuidVersion[8]]



def validate_uuid(val, version: Literal[1, 3, 4, 5, 6, 7, 8]) -> UUID:
    if not isinstance(val, UUID):
        raise ValueError(f"Expected a UUID, got {type(val)}")
    if val.version != version:
        raise ValueError(f"Expected a UUID{version}, got UUID{val.version}")
    return val

UUID7_2 = Annotated[
    UUID,
    GetPydanticSchema(
        get_pydantic_core_schema=lambda _, handler: core_schema.with_info_plain_validator_function(
            lambda val, info: validate_uuid(UUID(val) if info.mode == "json" else val, version=7),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda val, info: str(val) if info.mode == "json" else val,
                info_arg=True,
            ),
        ),
        get_pydantic_json_schema=lambda _, handler: {**handler(core_schema.str_schema()), "format": "uuid7"},
    ),
]

UUID7 = UUID7_1


if __name__ == "__main__":
    class MyModel(BaseModel):
        uid3: UUID3
        uid6: UUID6
    # end class

    obj = MyModel(uid3=uuid.uuid3(uuid.NAMESPACE_DNS, "python.org"), uid6=uuid6.uuid6())
    print(repr(obj))
# end if