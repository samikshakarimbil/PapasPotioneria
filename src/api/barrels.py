from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    total_greenml = 0
    total_price = 0
    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 1, 0, 0]:
            total_greenml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity

    if total_greenml > 0:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory \
                                                SET num_green_ml = num_green_ml + :total_greenml, \
                                                gold = gold - :total_price"),
                                                 {"total_greenml": total_greenml, "total_price": total_price})
        print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    bprice = 0
    green_barrel = False
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_GREEN_BARREL":
            green_barrel = True
            bprice = barrel.price
            break
    
    if green_barrel:
        print("there is a green barrel")
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).mappings()
            result = result.fetchone()
        print(result["num_green_potions"])
        print(result["gold"])
        if result["num_green_potions"] < 10 and result["gold"] >= bprice:
            print("barrel plan is returning")
            return [
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
            ]
    
    return[]

