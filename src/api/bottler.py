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

    print(f"Potions delivered: {potions_delivered}, Order_id: {order_id}")

    sku = ""
    green_ml, red_ml, blue_ml, dark_ml = 0, 0, 0, 0

    # Price per ml (ppm) for each colour: change later if prices too low/high
    green_ppm = 0.4
    red_ppm = 0.4
    blue_ppm = 0.48
    dark_ppm = 0.5    
    t = "Potion delivery"

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            type = potion.potion_type
            qty = potion.quantity
            red_ml += type[0] * qty
            green_ml += type[1] * qty
            blue_ml += type[2] * qty
            dark_ml += type[3] * qty
            price = int(red_ppm*type[0] + green_ppm*type[1] + blue_ppm*type[2] + dark_ppm*type[3])
            sku = "R" + str(type[0]) + "_G" + str(type[1]) + "_B" + str(type[2]) + "_D" + str(type[3])

            connection.execute(sqlalchemy.text("INSERT INTO potions (sku, red_amt, green_amt, blue_amt, dark_amt, inventory, price, transaction) \
                                               VALUES (:sku, :red_amt, :green_amt, :blue_amt, :dark_amt, :inventory, :price, :t)"),
                                            {"sku": sku, "red_amt": type[0], "green_amt": type[1], 
                                             "blue_amt": type[2], "dark_amt": type[3],
                                             "inventory": potion.quantity, "price": price, "t": t})
                
        connection.execute(sqlalchemy.text("""INSERT INTO global_inventory(num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, transaction)
                                           VALUES(:redml, :greenml, :blueml, :darkml, :transaction)"""),
                    {"greenml": -green_ml, "redml": -red_ml, "blueml": -blue_ml, "darkml": -dark_ml, "transaction": t})
                    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT SUM(num_green_ml) AS num_green_ml,
                                                        SUM(num_red_ml) AS num_red_ml,
                                                        SUM(num_blue_ml) AS num_blue_ml,
                                                        SUM(num_dark_ml) AS num_dark_ml
                                                        FROM global_inventory""")).mappings().fetchone()
        
        sum = connection.execute(sqlalchemy.text("SELECT SUM(inventory) FROM potions")).mappings().fetchone()

        capacity = connection.execute(sqlalchemy.text("SELECT potion_cap FROM capacity")).scalar_one_or_none()

        if (sum["sum"]):
            capacity-= sum["sum"]

    # prevent bottling more than 20 potions at once
    capacity = min(capacity, 20)

    greenml = result["num_green_ml"]
    redml = result["num_red_ml"]
    blueml = result["num_blue_ml"]
    darkml = result["num_dark_ml"]

    total_ml = greenml + redml + blueml + darkml
    print("Total ml in inv: ", total_ml)
    if total_ml >= 100 and capacity > 0:

        red_proportion = int((redml / total_ml) * 100)
        green_proportion = int((greenml / total_ml) * 100)
        blue_proportion = int((blueml / total_ml) * 100)
        dark_proportion = int((darkml / total_ml) * 100)
        
        p_list = [red_proportion, green_proportion, blue_proportion, dark_proportion]
        plist, mlist = [], []
        ml_list = [redml, greenml, blueml, darkml]

        for p, ml in zip(p_list, ml_list):
            if p > 0:
                plist.append(p) 
                mlist.append(ml)

        leftover = 100 - (red_proportion + green_proportion + blue_proportion + dark_proportion)

        if not plist:
            type = [0, 0, 0, darkml] 
            remaining = 100 - darkml
            available_mls = [(blueml, 2), (redml, 0), (greenml, 1)]
            for ml, idx in available_mls:
                if ml > remaining:
                    type[idx] = remaining
                    remaining = 0
                    break
                else:
                    type[idx] = ml
                    remaining -= ml

            plan.append({
                "potion_type": type,
                "quantity": 1
            })
            return plan

        amount = (min(mlist)) // min(plist)
        max_color = max(plist)

        if leftover:
            new_proportion = max_color + leftover
            change = False
            if max_color == red_proportion:
                red_proportion += leftover
                if (new_proportion * amount) > redml:  
                    change = True
                    tochange = redml
                print(("New red proportion: ", red_proportion))
            
            elif max_color == green_proportion:
                green_proportion += leftover
                if (new_proportion * amount) > greenml: 
                    change = True
                    tochange = greenml
                print(("New green proportion: ", green_proportion))
            
            elif max_color == blue_proportion:
                blue_proportion += leftover
                if (new_proportion * amount) > blueml:
                    change = True
                    tochange = blueml
                print(("New blue proportion: ", blue_proportion))

            else:
                dark_proportion += leftover
                if (new_proportion * amount) > darkml:
                    change = True
                    tochange = darkml
                print(("New dark proportion: ", dark_proportion))

            if change:
                while (amount * new_proportion) > tochange:
                    amount -= 1
        
        if amount:
            if capacity < amount:
                amount = capacity
            plan.append({
                "potion_type": [red_proportion, green_proportion, blue_proportion, dark_proportion],
                "quantity": amount
            })

    print("Bottle plan: ", plan)
    return plan

if __name__ == "__main__":
    print(get_bottle_plan())