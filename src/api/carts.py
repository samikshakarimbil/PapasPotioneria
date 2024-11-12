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

    max_items = 5
    previous = ""
    next = ""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT potions.id AS line_item_id,
                                                    sku AS item_sku,
                                                    customer AS customer_name,
                                                    cart_items.quantity AS line_item_total, timestamp
                                                    FROM carts
                                                    JOIN cart_items ON carts.id = cart_id
                                                    JOIN potions ON cart_items.potion_id = potions.id""")).mappings().fetchall()
        
    if customer_name:
        result = [x for x in result if x.get("customer_name") == customer_name]        
    if potion_sku:
        result = [x for x in result if x.get("item_sku") == potion_sku]     

    if sort_order == "asc":
        result.sort(key=lambda x: x[sort_col])
    else:
        result.sort(key=lambda x: x[sort_col], reverse=True)

    print(f"Search page: {search_page}")
    
    for r in result:
        print(f"{r}\n")

    return {
        "previous": previous,
        "next": next,
        "results": result,
    }

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
        id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer, class, level) VALUES (:new_cart, :class, :level) RETURNING id"),
                            {"new_cart": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}).mappings().fetchone()
    print("Created cart with id", id["id"])
    return {"cart_id": int(id["id"])}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    print("Setting items for cart ", cart_id)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT id FROM carts WHERE id = :cart_id"),
                                  {"cart_id": cart_id}).mappings().fetchone()
        if not result:
            print(f"Error fetching cart{cart_id}")
            return {"success": False}

        potion = connection.execute(sqlalchemy.text("""SELECT id 
                                                    FROM potions 
                                                    WHERE sku = :sku
                                                    AND transaction = 'Potion delivery' """),
                           {"sku": item_sku}).mappings().fetchone()

        pid = potion["id"]
        qty = cart_item.quantity

        connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, quantity, potion_id) 
                                           VALUES (:cart_id, :qty, :potion_id)"""),
                                           {"cart_id": cart_id, "qty": qty, "potion_id": pid})

    return {"success": True}


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    with db.engine.begin() as connection:
        total_qty = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM cart_items WHERE cart_id = :cart_id"),
                                {"cart_id": cart_id}).mappings().fetchone()["sum"]

        potions = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_items WHERE cart_id = :cart_id"),
                                {"cart_id": cart_id}).mappings().fetchall()

        print("Checking out cart", cart_id)
        print("Total potions to check out:", total_qty)
        print("Potions being checked out:", potions)

        if total_qty:
            gold_paid = 0
            for potion in potions:
                qty = potion["quantity"]
                id = potion["potion_id"]
                pot = connection.execute(sqlalchemy.text("SELECT sku, price FROM potions WHERE id = :id"),
                                           {"id": id}).mappings().fetchone()
                gold_paid += pot["price"] * qty
                sku = pot["sku"]

                t = f"Cart checkout for id {cart_id}"   

                connection.execute(sqlalchemy.text("""INSERT INTO potions (sku, inventory, transaction)
                                                   VALUES (:sku, :qty, :t)"""),
                                                   {"sku": sku, "qty": -qty, "t": t})
                
            connection.execute(sqlalchemy.text("""INSERT INTO global_inventory (gold, transaction)
                                               VALUES (:gold, :transaction)"""),
                                               {"gold": gold_paid, "transaction": t})
            
            
            
            return {
                "total_potions_bought": total_qty,
                "total_gold_paid": gold_paid
                }
        
    return {"Cart not found"}