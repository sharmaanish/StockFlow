from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Convert DRF exceptions into a consistent API error structure.
    """

    response = exception_handler(exc, context)

    # If DRF does not know how to handle the exception,
    # keep the default Django behavior for now.
    if response is None:
        return response

    # Validation errors already contain useful field-level details.
    if response.status_code == 400:
        return response

    # Keep authentication and permission errors simple and consistent.
    if response.status_code in [401, 403]:
        detail = response.data.get(
            "detail",
            "Request was not authorized.",
        )

        response.data = {
            "error": {
                "code": response.status_code,
                "detail": detail,
            }
        }

        return response

    # Standardize other DRF errors such as 404 and 405.
    detail = response.data.get(
        "detail",
        "An error occurred.",
    )

    response.data = {
        "error": {
            "code": response.status_code,
            "detail": detail,
        }
    }

    return response