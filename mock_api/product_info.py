from mock_api.base import MockAPI
from shared.schemas.request import ProductInfoRequest
from shared.schemas.response import ProductInfoResponse


class ProductInfoAPI(MockAPI):
    """Mock for the 2nd REST API — product info per partner per product."""

    _request_model = ProductInfoRequest
    _response_model = ProductInfoResponse
    _app_title = "Product Info API"
    _route = "/product-info"

    def _build_response(self, response_model):
        response = super()._build_response(response_model)
        if response_model is ProductInfoResponse:
            prices = sorted(
                [response.min_price, response.default_price, response.max_price]
            )
            response = ProductInfoResponse(
                min_price=prices[0],
                default_price=prices[1],
                max_price=prices[2],
            )
        return response


product_info_api = ProductInfoAPI()
app = product_info_api.app
