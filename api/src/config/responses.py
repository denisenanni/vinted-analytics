"""Reusable OpenAPI response definitions for consistent error documentation."""

from ..models.schemas import ErrorDetail, ValidationError

STANDARD_RESPONSES = {
    400: {
        "model": ValidationError,
        "description": "Invalid request parameters or validation error"
    },
    404: {
        "model": ErrorDetail,
        "description": "Resource not found"
    },
    500: {
        "model": ErrorDetail,
        "description": "Internal server error"
    }
}

# For endpoints that might have no data but aren't errors
NO_DATA_RESPONSES = {
    **STANDARD_RESPONSES,
    200: {
        "description": "Success - may return empty results if no data available"
    }
}
