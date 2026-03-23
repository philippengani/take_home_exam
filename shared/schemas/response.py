from datetime import datetime

from pydantic import BaseModel, NonNegativeFloat


class PricerResponse(BaseModel):
    price: NonNegativeFloat

class MemberDataResponse(BaseModel):
    last_login_datetime: datetime
    last_purchase_datetime: datetime | None
    last_purchase_amount: NonNegativeFloat | None
    number_of_transactions: NonNegativeFloat | None
    total_transaction_amount: NonNegativeFloat | None

class ProductInfoResponse(BaseModel):
    min_price: NonNegativeFloat
    default_price: NonNegativeFloat
    max_price: NonNegativeFloat

class PricingMLModelResponse(BaseModel):
    price: NonNegativeFloat

class AuditLogResponse(BaseModel):
    status: str
    log_id: str

