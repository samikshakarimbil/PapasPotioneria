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

# These are all the barrels in the catalog.
    
# Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), 
# Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), 
# Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), 
    
# Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=10), 
# Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=10), 
# Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=10), 
    
# Barrel(sku='MEDIUM_RED_BARREL', ml_per_barrel=2500, potion_type=[1, 0, 0, 0], price=250, quantity=10), 
# Barrel(sku='MEDIUM_GREEN_BARREL', ml_per_barrel=2500, potion_type=[0, 1, 0, 0], price=250, quantity=10), 
# Barrel(sku='MEDIUM_BLUE_BARREL', ml_per_barrel=2500, potion_type=[0, 0, 1, 0], price=300, quantity=10), 

# Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)
# Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30), 
# Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), 
# Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), 

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    total_green_ml, total_red_ml, total_blue_ml = 0, 0, 0
    total_price = 0
    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 1, 0, 0]:
            total_green_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity
        if barrel.potion_type == [1, 0, 0, 0]:
            total_red_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity
        if barrel.potion_type == [0, 0, 1, 0]:
            total_blue_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory \
                                            SET num_green_ml = num_green_ml + :total_greenml, \
                                           num_red_ml = num_red_ml + :total_redml, \
                                           num_blue_ml = num_blue_ml + :total_blueml, \
                                           gold = gold - :total_price"), \
                                            {"total_greenml": total_green_ml, "total_redml": total_red_ml, "total_blueml": total_blue_ml,
                                              "total_price": total_price})
        print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    sku, sku2 = "", ""
    bought, bought2 = False, False
    bp = 0
    plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        result = result.fetchone()
    print(result)

    greenml = int(result["num_green_ml"])
    redml = int(result["num_red_ml"])
    blueml = int(result["num_blue_ml"])
    greenptns = int(result["num_green_potions"])
    redptns = int(result["num_red_potions"])
    blueptns = int(result["num_blue_potions"])
    gold = int(result["gold"])

    totalml = greenml + redml + blueml

    if(redml <= greenml and redml <= blueml):
        least_ml = 0
    least_ml = 1
    if(greenml <= redml and greenml <= blueml):
        least_ml = 1
    elif(blueml <= greenml and blueml <= redml):
        least_ml = 2
    print("Red ml: ", redml)
    print("Green ml: ", greenml)
    print("Blue ml: ", blueml)
    print("Least ml: ", least_ml)

    if(redptns <= greenptns and redptns <= blueptns):
        least_potions = 0
    least_potions = 1
    if(greenptns <= redptns and greenptns <= blueptns):
        least_potions = 1
    elif(blueptns <= greenml and blueptns <= redptns):
        least_potions = 2
    print("Red potions: ", redptns)
    print("Green potions: ", greenptns)
    print("Blue potions: ", blueptns)
    print("Least potions: ", least_potions)

    for barrel in wholesale_catalog:
        total = 0
        bp = barrel.price
        if barrel.potion_type == [1, 0, 0, 0]:
            if least_ml == 0 and not bought: 
                if least_potions != 0:
                    if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                        print("buying red barrel because least ml")
                        total += bp
                        totalml += barrel.ml_per_barrel
                        sku = barrel.sku
                        bought = True
                else:
                    if greenptns < blueptns:
                        least_potions = 1
                    else:
                        least_potions = 2

            if least_potions == 0 and not bought2:
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("buying red barrel because least potions")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku2 = barrel.sku
                    bought2 = True

        elif barrel.potion_type == [0, 1, 0, 0]:
            if least_ml == 1 and not bought:
                if least_potions != 1:
                    if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                        print("buying green barrel because least ml")
                        total += bp
                        totalml += barrel.ml_per_barrel
                        sku = barrel.sku
                        bought = True
                else:
                    if redptns < blueptns:
                        least_potions = 0
                    else:
                        least_potions = 2

            if least_potions == 1 and not bought2:
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("buying green barrel because least potions")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku2 = barrel.sku
                    bought2 = True

        elif barrel.potion_type == [0, 0, 1, 0]:
            if least_ml == 2 and not bought:
                if least_potions != 2:
                    if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                        print("buying blue barrel because least ml")
                        total += bp
                        totalml += barrel.ml_per_barrel
                        sku = barrel.sku
                        bought = True
                else:
                    if redptns < greenptns:
                        least_potions = 0
                    else:
                        least_potions = 1

            if least_potions == 2 and not bought2:
                if gold >= bp and ((totalml + barrel.ml_per_barrel) <= 10000):
                    print("buying blue barrel because least potions")
                    total += bp
                    totalml += barrel.ml_per_barrel
                    sku2 = barrel.sku
                    bought2 = True

        gold -= total

    print("barrel price: ", total)

    if bought:
        plan.append({
            "sku": sku,
            "quantity": 1
        })

    if bought2:
        plan.append({
            "sku": sku2,
            "quantity": 1
        })
    
    return plan
