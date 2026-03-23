from typing import Type, TypeVar

from pydantic import BaseModel

from mock_api.base import MockAPI
from shared.schemas.request import MemberDataRequest
from shared.schemas.response import MemberDataResponse

T = TypeVar("T", bound=BaseModel)


class MemberDataAPI(MockAPI):
    """Mock for the 1st REST API — member data per partner per member."""

    _request_model = MemberDataRequest
    _response_model = MemberDataResponse
    _app_title = "Member Data API"
    _route = "/member-data"

    def _build_response(self, response_model: Type[T]) -> T:
        response = super()._build_response(response_model)
        # Identify nullable fields
        nullable_fields = [
            name
            for name, field_info in response_model.model_fields.items()
            if self._unwrap_type(field_info.annotation)[1]  # type: ignore[arg-type]
        ]
        # If any nullable field is None, set all nullable fields to None
        if any(getattr(response, f) is None for f in nullable_fields):
            for f in nullable_fields:
                object.__setattr__(response, f, None)
        return response


member_data_api = MemberDataAPI()
app = member_data_api.app
