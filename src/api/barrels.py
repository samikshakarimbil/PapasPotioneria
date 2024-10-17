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
    print(wholesale_catalog)

    sku = ""
    bp = 0
    plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        result = result.fetchone()
    print(result)

    greenml = int(result["num_green_ml"])
    redml = int(result["num_red_ml"])
    blueml = int(result["num_blue_ml"])
    darkml = result["num_dark_ml"]
    gold = int(result["gold"])

    totalml = greenml + redml + blueml + darkml

    if(redml <= greenml and redml <= blueml):
        least_ml = 0
    if(greenml <= redml and greenml <= blueml):
        least_ml = 1
    elif(blueml <= greenml and blueml <= redml):
        least_ml = 2

    for barrel in wholesale_catalog:
        total = 0
        bp = barrel.price

        if barrel.potion_type == [0, 0, 0, 1] and darkml < 1000:
            if gold >= bp:
                plan.append({
                    "sku": barrel.sku,
                    "quantity": 1
                    })          
                totalml += barrel.ml_per_barrel
                gold -= bp
                
        if barrel.potion_type == [1, 0, 0, 0]:
            if least_ml == 0: 
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("Buying red barrel")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku = barrel.sku
                    bought = True

        elif barrel.potion_type == [0, 1, 0, 0]:
            if least_ml == 1:
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("Buying green barrel")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku = barrel.sku
                    bought = True

        elif barrel.potion_type == [0, 0, 1, 0]:
            if least_ml == 2:
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("Buying blue barrel")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku = barrel.sku
                    bought = True

        gold -= total

    print("barrel price: ", total)

    if bought:
        plan.append({
            "sku": sku,
            "quantity": 1
        })
    
    return plan
