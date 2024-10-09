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

    return {
        "success": True
    }


@router.post("/")
def create_cart(new_cart: Customer):
    """ """

    with db.engine.begin() as connection:
        id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:new_cart) RETURNING id"),
                            {"new_cart": new_cart.customer_name})
       
    id = id.fetchone()
    print("id: ", id[0])
    return {"cart_id": int(id[0])}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    print("Setting item quantity")
    print("Cart id: ", cart_id)

    with db.engine.begin() as connection:
        result=connection.execute(sqlalchemy.text("SELECT id FROM carts WHERE id = :cart_id"),
                                  {"cart_id": cart_id}).mappings()
        result = result.fetchone()

        if not result:
            return {"success": False}
        
        print("Result: ", result)
        
        qty = cart_item.quantity
        print("Quantity: ", qty)
        print("SKU: ", item_sku)

        if item_sku == "GREEN_POTION":
            connection.execute(sqlalchemy.text("UPDATE carts \
                                           SET num_green = num_green + :qty \
                                           WHERE id = :cart_id"),
                           {"qty": qty, "cart_id": cart_id})
            
        elif item_sku == "RED_POTION":
            connection.execute(sqlalchemy.text("UPDATE carts \
                                           SET num_red = num_red + :qty \
                                           WHERE id = :cart_id"),
                           {"qty": qty, "cart_id": cart_id})
            
        elif item_sku == "BLUE_POTION":
            connection.execute(sqlalchemy.text("UPDATE carts \
                                           SET num_blue = num_blue + :qty \
                                           WHERE id = :cart_id"),
                           {"qty": qty, "cart_id": cart_id})

    return {"success": True}


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_paid = int(cart_checkout.payment)
    total: 0
    with db.engine.begin() as connection:
        inv = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        inv = inv.fetchone()

        cart = connection.execute(sqlalchemy.text("SELECT * FROM carts WHERE id = :cart_id"),
                                {"cart_id": cart_id}).mappings()
        cart = cart.fetchone()

        if cart:
            print(cart_id)
            green_purchased = cart["num_green"]
            red_purchased =  cart["num_red"]
            blue_purchased = cart["num_blue"]
            total = green_purchased + red_purchased + blue_purchased
        
            connection.execute(sqlalchemy.text("UPDATE global_inventory \
                                           SET gold = gold + :pay, \
                                            num_green_potions = num_green_potions - :green, \
                                            num_red_potions = num_red_potions - :red, \
                                            num_blue_potions = num_blue_potions - :blue"),
                           {"pay": gold_paid, "green": green_purchased, "red": red_purchased, "blue": blue_purchased})
            
            connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :cart_id"),
                               {"cart_id": cart_id})
            
            return {
                "total_potions_bought": total,
                "total_gold_paid": gold_paid
                }
        
    return {"Cart not found"}