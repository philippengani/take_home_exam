class PricerServiceError(Exception):
    """Domain error surfaced to the API layer."""

    def __init__(
        self,
        *,
        status_code: int,
        detail: str,
        service_name: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.service_name = service_name
