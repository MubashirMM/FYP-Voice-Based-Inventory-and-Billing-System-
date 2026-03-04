from fastapi import HTTPException

# Urdu labels for status codes, used by the exception handler.
error_map = {
    400: "غلط درخواست",      # Bad Request
    401: "غیر مجاز",         # Unauthorized
    403: "رسائی ممنوع",      # Forbidden
    404: "موجود نہیں",       # Not Found
    405: "طریقہ کار ممنوع",  # Method Not Allowed
    409: "تنازعہ",           # Conflict
    422: "غلط ڈیٹا",         # Unprocessable Entity
    500: "سرور کی خرابی",     # Internal Server Error
    502: "غلط گیٹ وے",       # Bad Gateway
    503: "سروس دستیاب نہیں", # Service Unavailable
    504: "گیٹ وے ٹائم آؤٹ"   # Gateway Timeout
}


def http_error(status_code: int, detail: str) -> HTTPException:
    """Return an HTTPException with the given status_code and Urdu detail.

    The global exception handler in ``main`` will add an ``error`` field based
    on ``error_map`` so callers don't need to repeat it.

    Example::
        raise http_error(404, "آئٹم موجود نہیں ہے")
    """
    return HTTPException(status_code=status_code, detail=detail)
