import pytest
from fastapi.testclient import TestClient

from pricer_service.errors import PricerServiceError
from pricer_service.main import create_app
from pricer_service.service import PricingResult
from shared.schemas.request import AuditLogRequest, ProductId
from shared.schemas.response import PricerResponse


def test_price_endpoint_returns_price_and_runs_background_audit() -> None:
    service = FakePricerService()
    app = create_app(service=service)

    with TestClient(app) as client:
        response = client.post(
            "/price",
            json={
                "partner_id": "partner-1",
                "member_id": "member-1",
                "product_id": "BUY",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"price": 19.5}
    assert len(service.logged_audits) == 1


def test_price_endpoint_rejects_invalid_payload() -> None:
    app = create_app(service=FakePricerService())

    with TestClient(app) as client:
        response = client.post(
            "/price",
            json={"partner_id": "partner-1", "product_id": "BUY"},
        )

    assert response.status_code == 422


@pytest.mark.parametrize("status_code", [404, 502, 504])
def test_price_endpoint_maps_service_errors(status_code: int) -> None:
    app = create_app(
        service=FakePricerService(
            error=PricerServiceError(
                status_code=status_code,
                detail="upstream failed",
                service_name="member_data",
            )
        )
    )

    with TestClient(app) as client:
        response = client.post(
            "/price",
            json={
                "partner_id": "partner-1",
                "member_id": "member-1",
                "product_id": "BUY",
            },
        )

    assert response.status_code == status_code
    assert response.json()["detail"] == "upstream failed"


class FakePricerService:
    def __init__(self, error: PricerServiceError | None = None) -> None:
        self.error = error
        self.logged_audits: list[AuditLogRequest] = []

    async def price_request(self, request: object) -> PricingResult:
        del request
        if self.error is not None:
            raise self.error
        return PricingResult(
            response=PricerResponse(price=19.5),
            audit_request=AuditLogRequest(
                partner_id="partner-1",
                member_id="member-1",
                product_id=ProductId.BUY,
                computed_price=19.5,
                request_timestamp="2026-03-20T12:00:00Z",
                response_duration_ms=42.0,
            ),
        )

    async def log_audit(self, audit_request: AuditLogRequest) -> None:
        self.logged_audits.append(audit_request)
