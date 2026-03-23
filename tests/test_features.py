from datetime import datetime, timezone

from pricer_service.features import build_pricing_features
from shared.schemas.request import ProductId
from shared.schemas.response import MemberDataResponse, ProductInfoResponse


def test_build_pricing_features_with_purchase_history() -> None:
    features = build_pricing_features(
        member_data=MemberDataResponse(
            last_login_datetime=datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc),
            last_purchase_datetime=datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
            last_purchase_amount=40.0,
            number_of_transactions=4,
            total_transaction_amount=100.0,
        ),
        product_info=ProductInfoResponse(
            min_price=10.0,
            default_price=15.0,
            max_price=20.0,
        ),
        product_id=ProductId.BUY,
        now=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert features.min_price == 10.0
    assert features.default_price == 15.0
    assert features.max_price == 20.0
    assert features.days_since_last_login == 5
    assert features.days_since_last_transaction == 3
    assert features.avg_transaction_size == 25.0
    assert features.last_transaction_ratio == 1.6


def test_build_pricing_features_defaults_to_zero_for_missing_history() -> None:
    features = build_pricing_features(
        member_data=MemberDataResponse(
            last_login_datetime=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
            last_purchase_datetime=None,
            last_purchase_amount=None,
            number_of_transactions=None,
            total_transaction_amount=None,
        ),
        product_info=ProductInfoResponse(
            min_price=10.0,
            default_price=15.0,
            max_price=20.0,
        ),
        product_id=ProductId.GIFT,
        now=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert features.days_since_last_login == 2
    assert features.days_since_last_transaction == 0
    assert features.avg_transaction_size == 0.0
    assert features.last_transaction_ratio == 0.0


def test_build_pricing_features_clamps_zero_transactions() -> None:
    features = build_pricing_features(
        member_data=MemberDataResponse(
            last_login_datetime=datetime(2026, 3, 18, 12, 0, tzinfo=timezone.utc),
            last_purchase_datetime=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc),
            last_purchase_amount=25.0,
            number_of_transactions=0,
            total_transaction_amount=100.0,
        ),
        product_info=ProductInfoResponse(
            min_price=10.0,
            default_price=15.0,
            max_price=20.0,
        ),
        product_id=ProductId.ACCELERATOR,
        now=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert features.days_since_last_transaction == 0
    assert features.avg_transaction_size == 0.0
    assert features.last_transaction_ratio == 0.0


def test_build_pricing_features_treats_naive_datetimes_as_utc() -> None:
    features = build_pricing_features(
        member_data=MemberDataResponse(
            last_login_datetime=datetime(2026, 3, 19, 12, 0),
            last_purchase_datetime=datetime(2026, 3, 18, 12, 0),
            last_purchase_amount=10.0,
            number_of_transactions=2,
            total_transaction_amount=20.0,
        ),
        product_info=ProductInfoResponse(
            min_price=10.0,
            default_price=15.0,
            max_price=20.0,
        ),
        product_id=ProductId.BUY,
        now=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
    )

    assert features.days_since_last_login == 1
    assert features.days_since_last_transaction == 2
