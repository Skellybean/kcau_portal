from rest_framework.views import exception_handler


def _first_message(value):
    if isinstance(value, dict):
        for item in value.values():
            found = _first_message(item)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for item in value:
            found = _first_message(item)
            if found:
                return found
    elif value:
        return str(value)
    return None


def api_exception_handler(exc, context):
    """Give the mobile app one predictable shape: {"detail": "...", "errors": {...}}."""
    response = exception_handler(exc, context)
    if response is not None and response.status_code == 400 and isinstance(response.data, (dict, list)):
        errors = response.data
        if isinstance(errors, dict) and "detail" in errors and isinstance(errors["detail"], str):
            return response
        response.data = {
            "detail": _first_message(errors) or "The request could not be processed.",
            "errors": errors,
        }
    return response
