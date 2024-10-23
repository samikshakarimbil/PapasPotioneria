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
    total_green_ml, total_red_ml, total_blue_ml, total_dark_ml = 0, 0, 0, 0
    total_price = 0
    for barrel in barrels_delivered:
        total_price += barrel.price * barrel.quantity
        if barrel.potion_type == [0, 1, 0, 0]:
            total_green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [1, 0, 0, 0]:
            total_red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]:
            total_blue_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            total_dark_ml += barrel.ml_per_barrel * barrel.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory \
                                            SET num_green_ml = num_green_ml + :total_greenml, \
                                           num_red_ml = num_red_ml + :total_redml, \
                                           num_blue_ml = num_blue_ml + :total_blueml, \
                                           num_dark_ml = num_dark_ml + :total_darkml, \
                                           gold = gold - :total_price"), \
                                            {"total_greenml": total_green_ml, "total_redml": total_red_ml, 
                                             "total_blueml": total_blue_ml, "total_darkml": total_dark_ml,
                                              "total_price": total_price})
        print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    sorted_catalog = sorted(wholesale_catalog, key=lambda x: x.price)
    print("Sorted catalog: ", sorted_catalog)

    bp = 0
    plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        result = result.fetchone()

    print("Time to buy barrels! Current inventory: ", result)

    greenml = result["num_green_ml"]
    redml = result["num_red_ml"]
    blueml = result["num_blue_ml"]
    darkml = result["num_dark_ml"]
    gold = result["gold"]

    gold = gold - 100 if gold >= 100 else 0
    print(f"Budget: {gold}")

    totalml = greenml + redml + blueml + darkml
    capacity = 10000 - totalml
    print(f"{capacity} ml available")
    if capacity == 0 and gold == 0: # remove on resets
         return[]

    if(redml <= greenml and redml <= blueml):
        least_ml = 0
    elif(greenml <= redml and greenml <= blueml):
        least_ml = 1
    elif(blueml <= greenml and blueml <= redml):
        least_ml = 2

    print("Least ml: ", least_ml)

    for barrel in sorted_catalog:
        if capacity > 0:
            bp = barrel.price
            ml = barrel.ml_per_barrel
            
            if barrel.potion_type == [0, 0, 0, 1] and darkml < 5000:
                if gold >= bp:
                    print("Buying dark barrel")
                    plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                        })      
                    darkml += ml
                    capacity -= ml
                    gold -= bp
                    
            if barrel.potion_type == [1, 0, 0, 0] and least_ml == 0:
                    if gold >= bp:
                        print("Buying red barrel")
                        plan.append({
                            "sku": barrel.sku,
                            "quantity": 1
                        })
                        redml += ml
                        capacity -= ml
                        gold -= bp
                        least_ml = 1 if greenml < blueml else 2
                    
            elif barrel.potion_type == [0, 1, 0, 0] and least_ml == 1:
                    if gold >= bp:
                        print("Buying green barrel")
                        plan.append({
                            "sku": barrel.sku,
                            "quantity": 1
                        })
                        greenml += ml
                        capacity -= ml
                        gold -= bp
                        least_ml = 0 if redml < blueml else 2

            elif barrel.potion_type == [0, 0, 1, 0] and least_ml == 2:
                    if gold >= bp:
                        print("Buying blue barrel")
                        plan.append({
                            "sku": barrel.sku,
                            "quantity": 1
                        })
                        blueml += ml
                        capacity -= ml
                        gold -= bp
                        least_ml = 1 if greenml < redml else 0

    print("Barrel plan: ", plan)
    return plan
