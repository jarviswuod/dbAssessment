"""
drf-spectacular schema helpers.

• Reusable error-response serializers so Swagger / ReDoc document every sad path.
• A postprocessing hook that automatically injects 400 / 401 / 403 / 404 / 500
  error responses into every operation — no per-view boilerplate required.
"""

from rest_framework import serializers


# ── Reusable error-envelope components ───────────────────────────────────────

class ErrorDetailSerializer(serializers.Serializer):
    """Inner error object that appears in every error response."""
    code = serializers.CharField(
        help_text="Machine-readable error code (e.g. `validation_error`, `not_authenticated`)."
    )
    message = serializers.CharField(
        help_text="Human-readable summary of what went wrong."
    )
    details = serializers.DictField(
        required=False,
        help_text="Field-level errors (present only for validation errors).",
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Uniform error envelope returned by the global exception handler."""
    success = serializers.BooleanField(default=False, help_text="Always `false` for errors.")
    error = ErrorDetailSerializer()


# ── Postprocessing hook ──────────────────────────────────────────────────────

# Which status codes to inject, mapped to a short description.
_ERROR_RESPONSES = {
    "400": "Bad request / validation error",
    "401": "Authentication credentials missing or invalid",
    "403": "Permission denied",
    "404": "Resource not found",
    "500": "Internal server error",
}

# Ref path that points to the shared ErrorResponse component.
_ERROR_REF = {"$ref": "#/components/schemas/ErrorResponse"}


def inject_error_responses(result, generator, **kwargs):
    """
    drf-spectacular postprocessing hook.

    Iterates over every operation in the generated schema and adds standard
    error-response entries for any status code not already declared.
    """
    # Ensure the ErrorResponse schema exists in components
    schemas = result.get("components", {}).get("schemas", {})
    if "ErrorResponse" not in schemas:
        schemas["ErrorResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "default": False,
                    "description": "Always `false` for errors.",
                },
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Machine-readable error code.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Human-readable summary.",
                        },
                        "details": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": "Field-level errors (validation only).",
                        },
                    },
                    "required": ["code", "message"],
                },
            },
            "required": ["success", "error"],
        }

    paths = result.get("paths", {})
    for _path, methods in paths.items():
        for _method, operation in methods.items():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            for status_code, description in _ERROR_RESPONSES.items():
                if status_code not in operation["responses"]:
                    operation["responses"][status_code] = {
                        "description": description,
                        "content": {
                            "application/json": {
                                "schema": _ERROR_REF,
                            }
                        },
                    }
    return result
