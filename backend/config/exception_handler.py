import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("django.request")

# ── Maps DRF exception classes to short, stable error codes ──
EXCEPTION_CODE_MAP = {
    DRFValidationError: "validation_error",
    ParseError: "parse_error",
    AuthenticationFailed: "authentication_failed",
    NotAuthenticated: "not_authenticated",
    DRFPermissionDenied: "permission_denied",
    NotFound: "not_found",
    MethodNotAllowed: "method_not_allowed",
    Throttled: "throttled",
    UnsupportedMediaType: "unsupported_media_type",
}


def _normalise_details(detail):
    """Recursively convert DRF error detail objects into plain serialisable data."""
    if isinstance(detail, list):
        return [_normalise_details(item) for item in detail]
    if isinstance(detail, dict):
        return {key: _normalise_details(value) for key, value in detail.items()}
    return str(detail)


def global_exception_handler(exc, context):
    """
    Central exception handler wired via REST_FRAMEWORK['EXCEPTION_HANDLER'].

    • Django exceptions (Http404, PermissionDenied, ValidationError) are
      converted to their DRF equivalents so everything flows through one path.
    • Every error response uses a uniform envelope:
        {
            "success": false,
            "error": {
                "code": "<stable_code>",
                "message": "<human-readable summary>",
                "details": { ... }          # present only when there are field-level errors
            }
        }
    • Unhandled (500) errors are logged and given a safe generic response.
    """

    # ── 1. Convert Django-native exceptions to DRF equivalents ──
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = DRFPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # ── 2. Let DRF handle known API exceptions ──
    response = drf_exception_handler(exc, context)

    if response is not None:
        code = EXCEPTION_CODE_MAP.get(type(exc), "error")
        detail = _normalise_details(exc.detail)

        # For validation errors the detail is the field→messages dict itself
        if isinstance(detail, dict) and code == "validation_error":
            message = "Invalid input."
            details = detail
        elif isinstance(detail, list):
            message = detail[0] if detail else "An error occurred."
            details = detail if len(detail) > 1 else None
        else:
            message = detail if isinstance(detail, str) else "An error occurred."
            details = None

        body = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
        if details is not None:
            body["error"]["details"] = details

        # Log all 4xx errors with appropriate levels
        request = context.get("request")
        user_id = getattr(getattr(request, "user", None), "id", None)
        path = getattr(request, "path", "unknown")
        method = getattr(request, "method", "unknown")

        if response.status_code >= 500:
            logger.error(
                "action=api_error user_id=%s method=%s path=%s status=%s code=%s message=%s",
                user_id, method, path, response.status_code, code, message,
            )
        elif code in ("authentication_failed", "not_authenticated", "permission_denied"):
            logger.warning(
                "action=api_error user_id=%s method=%s path=%s status=%s code=%s message=%s",
                user_id, method, path, response.status_code, code, message,
            )
        else:
            logger.info(
                "action=api_error user_id=%s method=%s path=%s status=%s code=%s message=%s",
                user_id, method, path, response.status_code, code, message,
            )

        response.data = body
        return response

    # ── 3. Unhandled / 500 errors ──
    # Log only the exception type and message — no stack traces or file paths
    # that could expose internal project structure.
    request = context.get("request")
    user_id = getattr(request, "user", None) and getattr(request.user, "id", None)
    logger.error(
        "action=unhandled_error user_id=%s error_type=%s message=%s",
        user_id,
        type(exc).__name__,
        str(exc),
    )

    return Response(
        {
            "success": False,
            "error": {
                "code": "server_error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
