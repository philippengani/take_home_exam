import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, cast

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from pricer_service.errors import PricerServiceError
from pricer_service.gateway import UpstreamGateway
from pricer_service.service import PricerService
from pricer_service.settings import Settings
from shared.schemas.request import PricerRequest
from shared.schemas.response import PricerResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def create_app(
    *,
    settings: Settings | None = None,
    service: PricerService | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if service is not None:
            app.state.pricer_service = service
            yield
            return

        timeout = httpx.Timeout(resolved_settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            gateway = UpstreamGateway(client=client, settings=resolved_settings)
            app.state.pricer_service = PricerService(gateway)
            yield

    app = FastAPI(title="Pricing Service", lifespan=lifespan)

    @app.post("/price", response_model=PricerResponse)
    async def price_endpoint(
        pricer_request: PricerRequest,
        background_tasks: BackgroundTasks,
        request: Request,
    ) -> PricerResponse:
        pricer_service = cast(PricerService, request.app.state.pricer_service)
        try:
            result = await pricer_service.price_request(pricer_request)
        except PricerServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        background_tasks.add_task(pricer_service.log_audit, result.audit_request)
        return result.response

    return app


app = create_app()
