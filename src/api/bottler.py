from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    total_potions = 0
    total_ml = 0
    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:
            total_potions += potion.quantity
            total_ml += potion.potion_type[1] * potion.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory \
                                           SET num_green_potions = num_green_potions + {total_potions} \
                                           num_green_ml = num_green_ml - {total_ml}"))
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
    
    green = result.first().num_green_ml
    num_green = int(green/100)
    if num_green:
        return [
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green,
                }
            ]
    return[]

if __name__ == "__main__":
    print(get_bottle_plan())