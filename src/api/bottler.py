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
    sku = ""
    green_potions, red_potions, blue_potions = 0, 0, 0
    green_ml, red_ml, blue_ml = 0, 0, 0

    # Price per ml (ppm) for each colour: change later if prices too low/high
    green_ppm = 1
    red_ppm = 1
    blue_ppm = 2
    dark_ppm = 3

    for potion in potions_delivered:
        type = potion.potion_type
        red_ml = type[0] * potion.quantity
        green_ml = type[1] * potion.quantity
        blue_ml = type[2] * potion.quantity
        

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


        for potion in potions_delivered:
            type = potion.potion_type
            price = red_ppm*type[0] + green_ppm*type[1] + blue_ppm*type[2] + dark_ppm*type[3]
            sku = "RED" + str(type[0]) + "_GREEN" + str(type[1]) + "_BLUE" + str(type[2]) + "_DARK" + str(type[3])
            result = connection.execute(sqlalchemy.text("SELECT sku FROM potions WHERE sku = :sku"),
                           {"sku": sku}).mappings()
            result = result.fetchall()
                        
            if not result:
                connection.execute(sqlalchemy.text("INSERT INTO potions (sku, red_amt, green_amt, blue_amt, dark_amt, inventory, price) \
                                               VALUES (:sku, :red_amt, :green_amt, :blue_amt, :dark_amt, :inventory, :price)"),
                                            {"sku": sku, "red_amt": type[0], "green_amt": type[1], 
                                             "blue_amt": type[2], "dark_amt": type[3],
                                             "inventory": potion.quantity, "price": price})
            else:
                connection.execute(sqlalchemy.text("UPDATE potions SET inventory = inventory + :qty WHERE sku = :sku"),
                                                   {"sku": sku, "qty": potion.quantity})
                
            # connection.execute(sqlalchemy.text("UPDATE global_inventory \
            #                                    SET num_potions = num_potions + :num"))
                
        
        print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    
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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        result = result.fetchone()

    plan = []
    greenml = result["num_green_ml"]
    redml = result["num_red_ml"]
    blueml = result["num_blue_ml"]
    print("Red ml in inv: ", redml)
    print("Green ml in inv: ", greenml)
    print("Blue ml in inv: ", blueml)

    greenptns = int(result["num_green_potions"])
    redptns = int(result["num_red_potions"])
    blueptns = int(result["num_blue_potions"])

    total_ml = greenml + redml + blueml
    total_potions = redptns + greenptns + blueptns
    capacity = 50 - total_potions
    print("Total ml in inv: ", total_ml)

    red_proportion = int((redml / total_ml) * 100)
    green_proportion = int((greenml / total_ml) * 100)
    blue_proportion = int((blueml / total_ml) * 100)
    leftover = 100 - (red_proportion + green_proportion + blue_proportion)
    print("Red proportion: ", red_proportion)
    print("Green proportion: ", green_proportion)
    print("Blue proportion: ", blue_proportion)
    print("Leftover: ", leftover)

    amount = (min(redml, greenml, blueml)) // min(red_proportion, green_proportion, blue_proportion)
    max_color = max(red_proportion, green_proportion, blue_proportion)
    print("Amount: ", amount)

    new_proportion = max_color + leftover
    changed = False
    if max_color == red_proportion:
        red_proportion += leftover
        if (new_proportion * amount) <= redml:  
            changed = True
        print(("New red proportion: ", red_proportion))
    
    elif max_color == green_proportion:
        green_proportion += leftover
        if (new_proportion * amount) <= greenml: 
            changed = True
        print(("New green proportion: ", green_proportion))
    
    elif max_color == blue_proportion:
        blue_proportion += leftover
        if (new_proportion * amount) <= redml:
            changed = True
        print(("New blue proportion: ", blue_proportion))

    if not changed:
        amount -= 1
    
    print("Amount: ", amount)
    if amount:
        if capacity < amount:
            amount = capacity
        plan.append({
            "potion_type": [red_proportion, green_proportion, blue_proportion, 0],
            "quantity": amount
        })

    print("Bottle plan: ", plan)
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())