import asyncio
import random
from datetime import date, datetime, timezone
from types import NoneType, UnionType
from typing import Annotated, Any, Type, TypeVar, Union, get_args, get_origin

from faker import Faker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

fake = Faker()


class MockAPI:
    _response_model: Type[BaseModel]
    _request_model: Type[BaseModel]
    _app_title: str = "Mock API"
    _route: str = "/get"

    def __init__(
        self,
        not_found_chance: float = 0.05,
        internal_error_chance: float = 0.05,
        timeout_chance: float = 0.05,
        timeout_seconds: float = 0.2,
    ):
        self.not_found_chance = not_found_chance
        self.internal_error_chance = internal_error_chance
        self.timeout_chance = timeout_chance
        self.timeout_seconds = timeout_seconds
        self.app = FastAPI(title=self._app_title)
        self._register_routes()

    def _maybe_fail(self) -> None:
        # Be evil
        roll = random.random()
        if roll < self.not_found_chance:
            raise HTTPException(status_code=404, detail="Requested resource not found")
        if roll < self.not_found_chance + self.internal_error_chance:
            raise HTTPException(status_code=500, detail="Internal server error")

    async def _maybe_delay(self) -> None:
        if random.random() < self.timeout_chance:
            await asyncio.sleep(self.timeout_seconds)

    _FAKER_BY_TYPE: dict[type, tuple[str, dict]] = {
        float: ("pyfloat", {"min_value": 0, "max_value": 1000}),
        int: ("pyint", {"min_value": 0, "max_value": 1000}),
        str: ("pystr", {}),
        bool: ("pybool", {}),
        date: ("date_object", {}),
        datetime: (
            "date_time_between",
            {"start_date": "-365d", "end_date": "now", "tzinfo": timezone.utc},
        ),
    }

    @staticmethod
    def _unwrap_type(field_type: type) -> tuple[type, bool]:
        """Return (base_type, nullable) for Annotated and optional fields."""
        nullable = False
        # Strip Annotated wrapper first
        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]
        # Handle Union[X, None] or X | None
        origin = get_origin(field_type)
        if origin is Union or isinstance(field_type, UnionType):
            args = [a for a in get_args(field_type) if a is not NoneType]
            if len(args) == 1:
                nullable = True
                field_type = args[0]
                # The inner type might itself be Annotated
                if get_origin(field_type) is Annotated:
                    field_type = get_args(field_type)[0]
        return field_type, nullable

    def _generate_field_value(self, field_type: type):
        base_type, nullable = self._unwrap_type(field_type)
        if nullable and random.random() < 0.3:
            return None
        entry = self._FAKER_BY_TYPE.get(base_type)
        if entry is None:
            return None
        method_name, kwargs = entry
        return getattr(fake, method_name)(**kwargs)

    def _build_response(self, response_model: Type[T]) -> T:
        data = {}
        for name, field_info in response_model.model_fields.items():
            data[name] = self._generate_field_value(field_info.annotation)  # type: ignore[arg-type]
        return response_model(**data)  # type: ignore[return-value]

    async def get(self, request: BaseModel) -> BaseModel:
        if not isinstance(request, BaseModel):
            raise HTTPException(status_code=422, detail="Invalid request format")
        self._maybe_fail()
        await self._maybe_delay()
        return self._build_response(self._response_model)

    def _register_routes(self) -> None:
        request_model = self._request_model
        response_model = self._response_model
        api = self

        @self.app.post(self._route, response_model=response_model)
        async def get_endpoint(request: request_model) -> Any:  # type: ignore[valid-type]
            return await api.get(request)

    @staticmethod
    def _validate_request(request_model: Type[BaseModel], data: dict) -> BaseModel:
        try:
            return request_model(**data)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
