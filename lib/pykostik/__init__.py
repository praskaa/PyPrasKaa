"""pyKostik root level config for all pykostik sub-modules."""

# Re-export all pyrevit modules for compatibility
from pyrevit import *

# Explicitly import and re-export modules that might not be included in *
try:
    from pyrevit import script
except ImportError:
    pass

try:
    from pyrevit import HOST_APP
except ImportError:
    pass

try:
    from pyrevit import DOCS
except ImportError:
    pass

# Import pykostik specific modules
from pykostik.revit.db.transaction import *
import exceptions as pke


def validate_type(obj, expected, err_msg=None):
    # type: (object, type | tuple[type], str) -> None

    if not isinstance(obj, expected):
        raise pke.TypeValidationError(
            message=err_msg,
            expected=expected,
            provided=type(obj)
        )
