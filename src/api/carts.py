from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

cart_id="0"

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }

cart_id=0

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """

    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """

    global cart_id
    cart_id = str(int(cart_id + 1))
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT id FROM carts")).mappings()
        result = result.fetchone()
        new_cart=1
        if result:
            for ids in result.id:
                if new_cart<ids:
                    new_cart = ids
        connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:new_cart)"),
                           {"new_cart": new_cart})
       
    return {"cart_id": new_cart}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    found = False
    with db.engine.begin() as connection:
        result=connection.execute(sqlalchemy.text("SELECT id FROM carts")).mappings()
        result = result.fetchone()
        if result:
                for id in result.values():
                    if id ==cart_id:
                        found = True

        if not found:
            return {"success": False}
        
        qty = cart_item.quantity
        connection.execute(sqlalchemy.text("UPDATE carts SET quantity = quantity + :qty"),
                           {"qty": qty})

    return {"success": True}


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_paid = cart_checkout.payment
    bought = 0
    with db.engine.begin() as connection:
        inv=connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).mappings()
        inv=inv.fetchone()

        cart=connection.execute(sqlalchemy.text("SELECT id, quantity FROM carts")).mappings()
        cart=cart.fetchone()

        if cart:
            print(cart_id)
            for id in cart.values():
                print(id)
                if id == cart_id:
                    bought = cart.quantity
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + :pay"),
                           {"pay": gold_paid})
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions - :bought"),
                           {"bought": bought})


    return {
        "total_potions_bought": bought,
        "total_gold_paid": gold_paid
    }