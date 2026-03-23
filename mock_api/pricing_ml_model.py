from mock_api.base import MockAPI
from shared.schemas.request import PricingMLModelRequest
from shared.schemas.response import PricingMLModelResponse


class PricingMLModelAPI(MockAPI):
    """Mock for the ML pricing model API."""

    _request_model = PricingMLModelRequest
    _response_model = PricingMLModelResponse
    _app_title = "Pricing ML Model API"
    _route = "/predict"


pricing_ml_model_api = PricingMLModelAPI()
app = pricing_ml_model_api.app
