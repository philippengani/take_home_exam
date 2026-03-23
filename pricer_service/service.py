import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Callable

from pricer_service.errors import PricerServiceError
from pricer_service.features import build_pricing_features, ensure_utc, utc_now
from pricer_service.gateway import UpstreamGateway
from shared.schemas.request import (
    AuditLogRequest,
    MemberDataRequest,
    PricerRequest,
    ProductInfoRequest,
)
from shared.schemas.response import PricerResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PricingResult:
    response: PricerResponse
    audit_request: AuditLogRequest


class PricerService:
    def __init__(
        self,
        gateway: UpstreamGateway,
        *,
        now_provider: Callable[[], datetime] = utc_now,
        perf_counter_provider: Callable[[], float] = perf_counter,
    ) -> None:
        self._gateway = gateway
        self._now_provider = now_provider
        self._perf_counter_provider = perf_counter_provider

    async def price_request(self, request: PricerRequest) -> PricingResult:
        request_started_at = self._perf_counter_provider()
        request_timestamp = ensure_utc(self._now_provider())

        logger.info(
            "pricing_request_started partner_id=%s member_id=%s product_id=%s",
            request.partner_id,
            request.member_id,
            request.product_id,
        )

        try:
            member_data, product_info = await asyncio.gather(
                self._gateway.fetch_member_data(
                    MemberDataRequest(
                        partner_id=request.partner_id,
                        member_id=request.member_id,
                    )
                ),
                self._gateway.fetch_product_info(
                    ProductInfoRequest(
                        partner_id=request.partner_id,
                        product_id=request.product_id,
                    )
                ),
            )
            feature_request = build_pricing_features(
                member_data=member_data,
                product_info=product_info,
                product_id=request.product_id,
                now=request_timestamp,
            )
            price_response = await self._gateway.predict_price(feature_request)
        except PricerServiceError:
            logger.exception(
                "pricing_request_failed partner_id=%s member_id=%s product_id=%s",
                request.partner_id,
                request.member_id,
                request.product_id,
            )
            raise

        response_duration_ms = (
            self._perf_counter_provider() - request_started_at
        ) * 1000
        audit_request = AuditLogRequest(
            partner_id=request.partner_id,
            member_id=request.member_id,
            product_id=request.product_id,
            computed_price=price_response.price,
            request_timestamp=_format_timestamp(request_timestamp),
            response_duration_ms=response_duration_ms,
        )

        logger.info(
            (
                "pricing_request_succeeded partner_id=%s member_id=%s "
                "product_id=%s latency_ms=%.3f"
            ),
            request.partner_id,
            request.member_id,
            request.product_id,
            response_duration_ms,
        )

        return PricingResult(
            response=PricerResponse(price=price_response.price),
            audit_request=audit_request,
        )

    async def log_audit(self, audit_request: AuditLogRequest) -> None:
        try:
            await self._gateway.log_audit(audit_request)
        except PricerServiceError:
            logger.warning(
                "audit_logging_failed partner_id=%s member_id=%s product_id=%s",
                audit_request.partner_id,
                audit_request.member_id,
                audit_request.product_id,
                exc_info=True,
            )


def _format_timestamp(value: datetime) -> str:
    utc_value = ensure_utc(value).astimezone(timezone.utc)
    return utc_value.isoformat().replace("+00:00", "Z")
