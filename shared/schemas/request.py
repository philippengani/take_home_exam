from enum import StrEnum

from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt


class ProductId(StrEnum):
    BUY = "BUY"
    GIFT = "GIFT"
    ACCELERATOR = "ACCELERATOR"


class PricerRequest(BaseModel):
    partner_id: str
    member_id: str
    product_id: ProductId


class MemberDataRequest(BaseModel):
    partner_id: str
    member_id: str


class ProductInfoRequest(BaseModel):
    partner_id: str
    product_id: ProductId


class PricingMLModelRequest(BaseModel):
    min_price: NonNegativeFloat
    default_price: NonNegativeFloat
    max_price: NonNegativeFloat
    product_id: ProductId
    days_since_last_login: NonNegativeInt
    days_since_last_transaction: NonNegativeInt
    avg_transaction_size: NonNegativeFloat
    last_transaction_ratio: NonNegativeFloat

class AuditLogRequest(BaseModel):
    partner_id: str
    member_id: str
    product_id: ProductId
    computed_price: NonNegativeFloat
    request_timestamp: str
    response_duration_ms: NonNegativeFloat

