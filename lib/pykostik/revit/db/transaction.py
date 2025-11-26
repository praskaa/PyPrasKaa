from pyrevit.revit.db import transaction as prt
from pyrevit.revit.db import failure as prf
from pyrevit import HOST_APP, DB

from pykostik.revit.db import failure as pkf


class DryTransaction(object):
    """Wrapper for `pyrevit.revit.DryTransaction`
    that uses HOST_APP.doc for compatibility.
    """

    def __init__(self, name=None, doc=None, clear_after_rollback=False):
        if doc is None and HOST_APP.doc is not None:
            doc = HOST_APP.doc
        elif doc is None:
            # Fallback if HOST_APP.doc is None
            from pyrevit import DOCS
            doc = DOCS.doc
        self._dry_txn = prt.DryTransaction(name, doc, clear_after_rollback)

    def __enter__(self):
        return self._dry_txn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._dry_txn.__exit__(exc_type, exc_val, exc_tb)


class Transaction(prt.Transaction):
    """Same as `pyrevit.revit.Transaction`
    but can swallow specific errors.
    """

    def __init__(self, name=None,
                 doc=None,
                 clear_after_rollback=False,
                 show_error_dialog=False,
                 swallow_errors=[],
                 log_errors=True,
                 nested=False):
        if doc is None and HOST_APP.doc is not None:
            doc = HOST_APP.doc
        elif doc is None:
            # Fallback if HOST_APP.doc is None
            from pyrevit import DOCS
            doc = DOCS.doc
        # create nested transaction if one is already open
        if doc.IsModifiable or nested:
            self._rvtxn = \
                DB.SubTransaction(doc)
        else:
            self._rvtxn = \
                DB.Transaction(
                    doc, name if name else prt.DEFAULT_TRANSACTION_NAME)
            self._fhndlr_ops = self._rvtxn.GetFailureHandlingOptions()
            self._fhndlr_ops = \
                self._fhndlr_ops.SetClearAfterRollback(clear_after_rollback)
            self._fhndlr_ops = \
                self._fhndlr_ops.SetForcedModalHandling(show_error_dialog)
            if swallow_errors:
                if hasattr(swallow_errors, '__iter__'):
                    self._fhndlr_ops = \
                        self._fhndlr_ops.SetFailuresPreprocessor(
                            pkf.SpecificFailureSwallower(
                                specific_failures=swallow_errors)
                        )
                else:
                    self._fhndlr_ops = \
                        self._fhndlr_ops.SetFailuresPreprocessor(
                            prf.FailureSwallower()
                        )
            self._rvtxn.SetFailureHandlingOptions(self._fhndlr_ops)
        self._logerror = log_errors
