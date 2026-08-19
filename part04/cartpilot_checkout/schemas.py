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
#     order_id="CP-10234",
#     lines=[OrderLine(sku="sku-002", name="Insulated Water Bottle 1L", quantity=1, line_total=24.50)],
#     subtotal=24.50,
#     estimated_tax=1.96,
#     total=26.46,
#     shopper_message="Your CartPilot order is confirmed — thanks for shopping with us!"
# ).model_dump()

