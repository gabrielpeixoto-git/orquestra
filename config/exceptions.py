from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc: APIException, context: dict[str, object]) -> Response | None:
    """Custom exception handler for DRF."""

    response = drf_exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            "error": {
                "code": exc.__class__.__name__,
                "message": str(exc.detail),
                "details": response.data if hasattr(response, "data") else None,
            }
        }
        response.data = custom_response_data

    return response
