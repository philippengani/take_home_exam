import os
from dataclasses import dataclass

DEFAULT_MEMBER_DATA_URL = "http://127.0.0.1:8001/member-data"
DEFAULT_PRODUCT_INFO_URL = "http://127.0.0.1:8002/product-info"
DEFAULT_PRICING_MODEL_URL = "http://127.0.0.1:8003/predict"
DEFAULT_AUDIT_LOG_URL = "http://127.0.0.1:8004/audit-log"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 0.25


@dataclass(frozen=True, slots=True)
class Settings:
    member_data_url: str = DEFAULT_MEMBER_DATA_URL
    product_info_url: str = DEFAULT_PRODUCT_INFO_URL
    pricing_model_url: str = DEFAULT_PRICING_MODEL_URL
    audit_log_url: str = DEFAULT_AUDIT_LOG_URL
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            member_data_url=os.getenv("MEMBER_DATA_URL", DEFAULT_MEMBER_DATA_URL),
            product_info_url=os.getenv("PRODUCT_INFO_URL", DEFAULT_PRODUCT_INFO_URL),
            pricing_model_url=os.getenv("PRICING_MODEL_URL", DEFAULT_PRICING_MODEL_URL),
            audit_log_url=os.getenv("AUDIT_LOG_URL", DEFAULT_AUDIT_LOG_URL),
            request_timeout_seconds=float(
                os.getenv(
                    "REQUEST_TIMEOUT_SECONDS",
                    str(DEFAULT_REQUEST_TIMEOUT_SECONDS),
                )
            ),
        )
