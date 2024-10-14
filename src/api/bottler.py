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

    green_potions, red_potions, blue_potions = 0, 0, 0
    green_ml, red_ml, blue_ml = 0, 0, 0
    for potion in potions_delivered:
        if potion.potion_type == [100, 0, 0, 0]:
            red_potions += potion.quantity
            red_ml += red_potions * 100
        if potion.potion_type == [0, 100, 0, 0]:
            green_potions += potion.quantity
            green_ml += green_potions * 100
        if potion.potion_type == [0, 0, 100, 0]:
            blue_potions += potion.quantity
            blue_ml += blue_potions * 100

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory \
            SET num_green_potions = num_green_potions + :gp, \
                num_red_potions = num_red_potions + :rp, \
                num_blue_potions = num_blue_potions + :bp, \
                num_green_ml = num_green_ml - :greenml, \
                num_red_ml = num_red_ml - :redml, \
                num_blue_ml = num_blue_ml - :blueml"),
                {"gp": green_potions, "rp": red_potions, "bp": blue_potions, \
                 "greenml": green_ml, "redml": red_ml, "blueml": blue_ml})
        
        print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml FROM global_inventory")).mappings()
        result = result.fetchone()

    plan = []
    greenml = result["num_green_ml"]
    redml = result["num_red_ml"]
    blueml = result["num_blue_ml"]
    print("green ml in inv: ", greenml)
    print("red ml in inv: ", redml)
    print("blue ml in inv: ", blueml)

    totalcost = 0  # hold cost of the unique potion based on the mix

    if greenml:
        totalcost += 30
        num_green = int(greenml/100)
        plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": num_green
        })


    
    if redml:
        totalcost += 30
        num_red = int(redml/100)
        plan.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": num_red
        })

    if blueml:
        totalcost += 50
        num_blue = int(blueml/100)
        plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": num_blue
        })

    print("plan: ", plan)
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())