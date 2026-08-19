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
#     lines=[OrderLine(sku="sku-004", name="Merino Wool Hiking Socks (3-pack)", quantity=2, line_total=37.50)],
#     subtotal=37.50,
#     estimated_tax=3.00,
#     total=40.50,
#     shopper_message="Thanks for your order! Your confirmation is CP-10234."
# ).model_dump()

