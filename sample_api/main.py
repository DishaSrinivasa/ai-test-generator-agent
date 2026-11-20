"""Papa David's Pizza — sample REST API used as the test target."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(
    title="Papa David's Pizza API",
    description="Ordering API for Papa David's Pizza — Henderson, CO",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

MENU: dict[str, dict] = {
    "cheese-pizza":        {"name": "Cheese Pizza",        "price": 9.99,  "category": "pizza"},
    "pepperoni-pizza":     {"name": "Pepperoni Lovers",    "price": 15.99, "category": "pizza"},
    "meat-lovers-pizza":   {"name": "Meat Lovers Pizza",   "price": 15.99, "category": "pizza"},
    "traditional-wings":   {"name": "Traditional Wings",   "price": 9.99,  "category": "wings"},
    "boneless-wings":      {"name": "Boneless Wings",      "price": 8.99,  "category": "wings"},
    "philly-steak":        {"name": "Philly Steak Sandwich","price": 12.99, "category": "sandwich"},
    "ranch-sauce":         {"name": "Ranch Dipping Sauce", "price": 2.00,  "category": "sauce"},
}

_orders: dict[str, dict] = {}
_next_id = 1


class OrderItem(BaseModel):
    item_id: str
    quantity: int = Field(ge=1, le=20)


class OrderRequest(BaseModel):
    items: list[OrderItem] = Field(min_length=1)
    pickup_or_delivery: Literal["pickup", "delivery"] = "pickup"
    customer_name: str = Field(min_length=1, max_length=100)


class OrderResponse(BaseModel):
    order_id: str
    status: str
    total: float
    items: list[OrderItem]
    pickup_or_delivery: str
    customer_name: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/menu", summary="List all menu items")
def list_menu():
    return {"items": MENU}


@app.get("/menu/{item_id}", summary="Get a single menu item")
def get_menu_item(item_id: str):
    item = MENU.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, **item}


@app.post("/orders", response_model=OrderResponse, status_code=201, summary="Place an order")
def create_order(req: OrderRequest):
    global _next_id
    for oi in req.items:
        if oi.item_id not in MENU:
            raise HTTPException(status_code=422, detail=f"Unknown item: {oi.item_id}")
    total = sum(MENU[oi.item_id]["price"] * oi.quantity for oi in req.items)
    order_id = f"ORD-{_next_id:04d}"
    _next_id += 1
    order = {
        "order_id": order_id,
        "status": "received",
        "total": round(total, 2),
        "items": [oi.model_dump() for oi in req.items],
        "pickup_or_delivery": req.pickup_or_delivery,
        "customer_name": req.customer_name,
    }
    _orders[order_id] = order
    return order


@app.get("/orders/{order_id}", response_model=OrderResponse, summary="Get order status")
def get_order(order_id: str):
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete("/orders/{order_id}", status_code=204, summary="Cancel an order")
def cancel_order(order_id: str):
    if order_id not in _orders:
        raise HTTPException(status_code=404, detail="Order not found")
    del _orders[order_id]
