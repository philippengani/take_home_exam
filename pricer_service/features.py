from datetime import datetime, timezone

from shared.schemas.request import PricingMLModelRequest, ProductId
from shared.schemas.response import MemberDataResponse, ProductInfoResponse


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def days_since(*, timestamp: datetime, now: datetime) -> int:
    return max(0, (now - ensure_utc(timestamp)).days)


def build_pricing_features(
    *,
    member_data: MemberDataResponse,
    product_info: ProductInfoResponse,
    product_id: ProductId,
    now: datetime | None = None,
) -> PricingMLModelRequest:
    current_time = ensure_utc(now or utc_now())
    last_purchase_datetime = member_data.last_purchase_datetime
    last_purchase_amount = member_data.last_purchase_amount
    number_of_transactions = member_data.number_of_transactions
    total_transaction_amount = member_data.total_transaction_amount
    has_valid_transactions = (
        last_purchase_datetime is not None
        and last_purchase_amount is not None
        and number_of_transactions is not None
        and total_transaction_amount is not None
        and number_of_transactions > 0
    )

    if not has_valid_transactions:
        days_since_last_transaction = 0
        avg_transaction_size = 0.0
        last_transaction_ratio = 0.0
    else:
        assert last_purchase_datetime is not None
        assert last_purchase_amount is not None
        assert number_of_transactions is not None
        assert total_transaction_amount is not None
        days_since_last_transaction = days_since(
            timestamp=last_purchase_datetime,
            now=current_time,
        )
        avg_transaction_size = total_transaction_amount / number_of_transactions
        if avg_transaction_size <= 0:
            avg_transaction_size = 0.0
            last_transaction_ratio = 0.0
        else:
            last_transaction_ratio = last_purchase_amount / avg_transaction_size

    return PricingMLModelRequest(
        min_price=product_info.min_price,
        default_price=product_info.default_price,
        max_price=product_info.max_price,
        product_id=product_id,
        days_since_last_login=days_since(
            timestamp=member_data.last_login_datetime,
            now=current_time,
        ),
        days_since_last_transaction=days_since_last_transaction,
        avg_transaction_size=avg_transaction_size,
        last_transaction_ratio=last_transaction_ratio,
    )
