"""
Part 9 — resilient tools.

Two conventions do most of the work:
1. Tools NEVER raise raw exceptions back to the model. They catch
   everything and return a structured {"status": "error", ...} dict —
   the model can reason about a dict; it can't reason about a stack trace.
2. Retries happen in the tool, with a hard bounded budget — not as an
   open-ended "keep trying" loop the model talks itself into. Retrying
   forever is itself a cost bug, not just a bug.
"""

# Standard library utilities for randomness, sleeping, and decorators
import random
import time
from functools import wraps



class RetryBudgetExceeded(Exception):
    pass


def with_retries(max_attempts: int = 3, base_delay: float = 0.2):
    """Retries a flaky call with exponential backoff, up to a hard cap.
    This is the ENTIRE retry policy for the wrapped function — once
    max_attempts is spent, we stop and report failure structurally
    rather than letting the caller (or the model) retry indefinitely."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - intentionally broad, this is the boundary
                    last_error = exc
                    if attempt < max_attempts:
                        time.sleep(base_delay * (2 ** (attempt - 1)))
            raise RetryBudgetExceeded(str(last_error))

        return wrapper

    return decorator


def _flaky_payment_gateway_call(order_total: float) -> dict:
    """Simulates an unreliable external payment gateway — fails ~30% of
    the time with a transient error, to demonstrate the retry path."""
    if random.random() < 0.3:
        raise ConnectionError("payment gateway timeout")
    return {"transaction_id": f"txn_{random.randint(100000, 999999)}", "amount_charged": order_total}


@with_retries(max_attempts=3)
def _charge_with_retries(order_total: float) -> dict:
    return _flaky_payment_gateway_call(order_total)


def charge_payment(order_total: float) -> dict:
    """Charges the shopper's payment method for the order total.

    Args:
        order_total: The total amount to charge, in dollars.

    Returns:
        On success: {"status": "success", "transaction_id": ..., "amount_charged": ...}
        On failure: {"status": "error", "error_type": "payment_failed",
                     "retryable": bool, "message": str} — a structured
        failure the model can react to (e.g. apologize and suggest
        trying again later), never a raised exception.
    """
    try:
        result = _charge_with_retries(order_total)
        return {"status": "success", **result}
    except RetryBudgetExceeded as exc:
        return {
            "status": "error",
            "error_type": "payment_failed",
            "retryable": False,  # we already exhausted our retry budget
            "message": f"Payment could not be processed after multiple attempts: {exc}",
        }

# --- Sample Resilient Execution Output ---
# Success Case:
# charge_payment(89.99) ->
# {"status": "success", "transaction_id": "txn_849201", "amount_charged": 89.99}
#
# Flaky Failure / Budget Exceeded Case:
# charge_payment(89.99) ->
# {"status": "error", "error_type": "payment_failed", "retryable": False, "message": "Payment could not be processed after multiple attempts: payment gateway timeout"}

