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

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
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

    return "OK"
