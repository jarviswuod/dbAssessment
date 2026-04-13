from datetime import datetime


def serialize_value(val):
    """Convert non-JSON-serializable values to strings."""
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if hasattr(val, "__str__") and not isinstance(val, (str, int, float, bool, list, dict, type(None))):
        return str(val)
    return val
