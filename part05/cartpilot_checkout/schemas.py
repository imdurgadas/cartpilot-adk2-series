# Pydantic schema validation for structured outputs
from pydantic import BaseModel, Field



class OrderLine(BaseModel):
    sku: str
    name: str
    quantity: int
    line_total: float


class OrderConfirmation(BaseModel):
    """Structured order confirmation — this is what downstream systems
    (email receipts, order DB, analytics) actually consume, so it must
    be guaranteed-valid, not "usually valid JSON the model produced"."""

    order_id: str = Field(description="A short, human-readable order reference, e.g. CP-10234.")
    lines: list[OrderLine]
    subtotal: float
    estimated_tax: float
    total: float
    shopper_message: str = Field(
        description="A short, friendly one-line confirmation message for the shopper."
    )

# --- Sample Validated Schema Dump ---
# OrderConfirmation(
#     order_id="CP-48201",
#     lines=[OrderLine(sku="sku-001", name="Trail Runner Jacket", quantity=1, line_total=89.99)],
#     subtotal=80.99,
#     estimated_tax=6.48,
#     total=87.47,
#     shopper_message="Order CP-48201 confirmed! Your 10% discount was applied."
# ).model_dump()

