import asyncio
from datetime import datetime

from mock_api.member_data import MemberDataAPI
from mock_api.product_info import ProductInfoAPI
from shared.schemas.request import MemberDataRequest, ProductId, ProductInfoRequest
from shared.schemas.response import MemberDataResponse, ProductInfoResponse


def test_member_data_api_builds_valid_response() -> None:
    api = MemberDataAPI(
        not_found_chance=0,
        internal_error_chance=0,
        timeout_chance=0,
    )

    response = asyncio.run(
        api.get(MemberDataRequest(partner_id="partner-1", member_id="member-1"))
    )

    assert isinstance(response, MemberDataResponse)
    assert isinstance(response.last_login_datetime, datetime)
    if response.last_purchase_datetime is None:
        assert response.last_purchase_amount is None
        assert response.number_of_transactions is None
        assert response.total_transaction_amount is None


def test_product_info_api_returns_sorted_prices() -> None:
    api = ProductInfoAPI(
        not_found_chance=0,
        internal_error_chance=0,
        timeout_chance=0,
    )

    response = asyncio.run(
        api.get(
            ProductInfoRequest(
                partner_id="partner-1",
                product_id=ProductId.BUY,
            )
        )
    )

    assert isinstance(response, ProductInfoResponse)
    assert response.min_price <= response.default_price <= response.max_price
