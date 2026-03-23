import asyncio
import logging
from datetime import datetime, timezone

import pytest

from pricer_service.errors import PricerServiceError
from pricer_service.service import PricerService
from shared.schemas.request import (
    AuditLogRequest,
    PricerRequest,
    PricingMLModelRequest,
    ProductId,
)
from shared.schemas.response import (
    AuditLogResponse,
    MemberDataResponse,
    PricingMLModelResponse,
    ProductInfoResponse,
)


def test_price_request_builds_features_and_audit_payload() -> None:
    gateway = StubGateway()
    counter = iter([100.0, 100.123])
    service = PricerService(
        gateway,
        now_provider=lambda: datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        perf_counter_provider=lambda: next(counter),
    )

    result = asyncio.run(
        service.price_request(
            PricerRequest(
                partner_id="partner-1",
                member_id="member-1",
                product_id=ProductId.BUY,
            )
        )
    )

    assert result.response.price == 17.5
    assert result.audit_request.partner_id == "partner-1"
    assert result.audit_request.member_id == "member-1"
    assert result.audit_request.product_id == ProductId.BUY
    assert result.audit_request.request_timestamp == "2026-03-20T12:00:00Z"
    assert result.audit_request.response_duration_ms == pytest.approx(123.0)
    assert gateway.pricing_requests == [
        PricingMLModelRequest(
            min_price=10.0,
            default_price=15.0,
            max_price=20.0,
            product_id=ProductId.BUY,
            days_since_last_login=5,
            days_since_last_transaction=3,
            avg_transaction_size=25.0,
            last_transaction_ratio=1.6,
        )
    ]


def test_price_request_fetches_member_and_product_concurrently() -> None:
    service = PricerService(
        ConcurrentGateway(),
        now_provider=lambda: datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
    )

    result = asyncio.run(
        service.price_request(
            PricerRequest(
                partner_id="partner-1",
                member_id="member-1",
                product_id=ProductId.BUY,
            )
        )
    )

    assert result.response.price == 17.5


@pytest.mark.parametrize("status_code", [404, 502, 504])
def test_price_request_propagates_upstream_errors(status_code: int) -> None:
    gateway = StubGateway(
        member_error=PricerServiceError(
            status_code=status_code,
            detail="member_data failed",
            service_name="member_data",
        )
    )
    service = PricerService(gateway)

    with pytest.raises(PricerServiceError) as exc_info:
        asyncio.run(
            service.price_request(
                PricerRequest(
                    partner_id="partner-1",
                    member_id="member-1",
                    product_id=ProductId.BUY,
                )
            )
        )

    assert exc_info.value.status_code == status_code


def test_log_audit_swallows_audit_failures(caplog: pytest.LogCaptureFixture) -> None:
    gateway = StubGateway(
        audit_error=PricerServiceError(
            status_code=502,
            detail="audit failed",
            service_name="audit_log",
        )
    )
    service = PricerService(gateway)
    audit_request = AuditLogRequest(
        partner_id="partner-1",
        member_id="member-1",
        product_id=ProductId.BUY,
        computed_price=10.0,
        request_timestamp="2026-03-20T12:00:00Z",
        response_duration_ms=10.0,
    )

    with caplog.at_level(logging.WARNING):
        asyncio.run(service.log_audit(audit_request))

    assert "audit_logging_failed" in caplog.text


class StubGateway:
    def __init__(
        self,
        *,
        member_error: PricerServiceError | None = None,
        product_error: PricerServiceError | None = None,
        pricing_error: PricerServiceError | None = None,
        audit_error: PricerServiceError | None = None,
    ) -> None:
        self.member_error = member_error
        self.product_error = product_error
        self.pricing_error = pricing_error
        self.audit_error = audit_error
        self.pricing_requests: list[PricingMLModelRequest] = []

    async def fetch_member_data(self, request: object) -> MemberDataResponse:
        del request
        if self.member_error is not None:
            raise self.member_error
        return MemberDataResponse(
            last_login_datetime=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
            last_purchase_datetime=datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
            last_purchase_amount=40.0,
            number_of_transactions=4,
            total_transaction_amount=100.0,
        )

    async def fetch_product_info(self, request: object) -> ProductInfoResponse:
        del request
        if self.product_error is not None:
            raise self.product_error
        return ProductInfoResponse(min_price=10.0, default_price=15.0, max_price=20.0)

    async def predict_price(
        self,
        request: PricingMLModelRequest,
    ) -> PricingMLModelResponse:
        self.pricing_requests.append(request)
        if self.pricing_error is not None:
            raise self.pricing_error
        return PricingMLModelResponse(price=17.5)

    async def log_audit(self, request: AuditLogRequest) -> AuditLogResponse:
        del request
        if self.audit_error is not None:
            raise self.audit_error
        return AuditLogResponse(status="logged", log_id="log-1")


class ConcurrentGateway(StubGateway):
    def __init__(self) -> None:
        super().__init__()
        self._started: set[str] = set()
        self._both_started = asyncio.Event()

    async def fetch_member_data(self, request: object) -> MemberDataResponse:
        await self._wait_until_both_started("member")
        return await super().fetch_member_data(request)

    async def fetch_product_info(self, request: object) -> ProductInfoResponse:
        await self._wait_until_both_started("product")
        return await super().fetch_product_info(request)

    async def _wait_until_both_started(self, name: str) -> None:
        self._started.add(name)
        if len(self._started) == 2:
            self._both_started.set()
        await asyncio.wait_for(self._both_started.wait(), timeout=0.1)
