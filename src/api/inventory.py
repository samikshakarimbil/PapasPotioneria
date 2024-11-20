from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT SUM(gold) AS gold,
                                                    SUM(num_green_ml) AS num_green_ml,
                                                    SUM(num_red_ml) AS num_red_ml,
                                                    SUM(num_blue_ml) AS num_blue_ml,
                                                    SUM(num_dark_ml) AS num_dark_ml
                                                    FROM global_inventory""")).mappings().fetchone()

        potions = connection.execute(sqlalchemy.text("SELECT SUM(inventory) FROM potions")).mappings().fetchone()

        potions = potions["sum"]
        ml = result["num_green_ml"] + result["num_blue_ml"] + result["num_red_ml"] + result["num_dark_ml"]
        gold = result["gold"]
    
    return {
        "number_of_potions": potions, 
        "ml_in_barrels": ml, 
        "gold": gold
        }

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    pcap = 0
    mlcap = 0

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT SUM(gold) AS gold FROM global_inventory")).scalar_one_or_none()
        cap = connection.execute(sqlalchemy.text("SELECT potion_cap, ml_cap FROM capacity")).mappings().fetchone()

    print(f"Gold: {gold}, cap: {cap}")
    mlgoldcap = (cap["ml_cap"] / 10000) * 4000
    pgoldcap = (cap["potion_cap"] / 50) * 4000

    if gold > mlgoldcap:
        mlcap = 1    
        gold -= 1000
    if gold > pgoldcap:
        pcap = 1
        gold -= 1000

    return {
        "potion_capacity": pcap,
        "ml_capacity": mlcap
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    print("Capacity delivery")

    pcap = capacity_purchase.potion_capacity
    mlcap = capacity_purchase.ml_capacity
    total = 1000 * (pcap + mlcap)
    totpcap = pcap * 50
    totmlcap = mlcap * 10000

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""INSERT INTO global_inventory(gold, transaction)
                                           VALUES (:total, 'Capacity purchase')"""),
                                           {"total": -total})
        connection.execute(sqlalchemy.text("""UPDATE capacity 
                                           SET potion_cap = potion_cap + :pcap,
                                           ml_cap = ml_cap + :mlcap,
                                           cap_reason = 'Capacity purchase'"""),
                                           {"pcap": totpcap, 
                                            "mlcap": totmlcap})

    return "OK"
 