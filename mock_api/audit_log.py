from mock_api.base import MockAPI, fake
from shared.schemas.request import AuditLogRequest
from shared.schemas.response import AuditLogResponse


class AuditLogAPI(MockAPI):
    """Mock for the audit/usage logging API."""

    _request_model = AuditLogRequest
    _response_model = AuditLogResponse
    _app_title = "Audit Log API"
    _route = "/audit-log"

    def _build_response(self, response_model):
        return AuditLogResponse(
            status="logged",
            log_id=fake.uuid4(),
        )


audit_log_api = AuditLogAPI()
app = audit_log_api.app
