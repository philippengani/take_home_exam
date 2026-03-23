import httpx
from pydantic import BaseModel, ValidationError

from pricer_service.errors import PricerServiceError
from pricer_service.settings import Settings
from shared.schemas.request import (
    AuditLogRequest,
    MemberDataRequest,
    PricingMLModelRequest,
    ProductInfoRequest,
)
from shared.schemas.response import (
    AuditLogResponse,
    MemberDataResponse,
    PricingMLModelResponse,
    ProductInfoResponse,
)


class UpstreamGateway:
    def __init__(self, *, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def fetch_member_data(
        self,
        request: MemberDataRequest,
    ) -> MemberDataResponse:
        return await self._post(
            service_name="member_data",
            url=self._settings.member_data_url,
            payload=request,
            response_model=MemberDataResponse,
        )

    async def fetch_product_info(
        self,
        request: ProductInfoRequest,
    ) -> ProductInfoResponse:
        return await self._post(
            service_name="product_info",
            url=self._settings.product_info_url,
            payload=request,
            response_model=ProductInfoResponse,
        )

    async def predict_price(
        self,
        request: PricingMLModelRequest,
    ) -> PricingMLModelResponse:
        return await self._post(
            service_name="pricing_model",
            url=self._settings.pricing_model_url,
            payload=request,
            response_model=PricingMLModelResponse,
        )

    async def log_audit(self, request: AuditLogRequest) -> AuditLogResponse:
        return await self._post(
            service_name="audit_log",
            url=self._settings.audit_log_url,
            payload=request,
            response_model=AuditLogResponse,
        )

    async def _post[T: BaseModel](
        self,
        *,
        service_name: str,
        url: str,
        payload: BaseModel,
        response_model: type[T],
    ) -> T:
        try:
            response = await self._client.post(
                url,
                json=payload.model_dump(mode="json"),
            )
        except httpx.RequestError as exc:
            raise PricerServiceError(
                status_code=504,
                detail=f"{service_name} request failed",
                service_name=service_name,
            ) from exc

        if response.status_code == 404:
            raise PricerServiceError(
                status_code=404,
                detail=f"{service_name} resource not found",
                service_name=service_name,
            )
        if response.status_code >= 400:
            raise PricerServiceError(
                status_code=502,
                detail=f"{service_name} upstream error",
                service_name=service_name,
            )

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise PricerServiceError(
                status_code=502,
                detail=f"{service_name} returned invalid JSON",
                service_name=service_name,
            ) from exc

        try:
            return response_model.model_validate(response_payload)
        except ValidationError as exc:
            raise PricerServiceError(
                status_code=502,
                detail=f"{service_name} returned an invalid payload",
                service_name=service_name,
            ) from exc
