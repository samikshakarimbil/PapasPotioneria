from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).mappings()
        result = result.fetchone()
        
    catalog = []
    gp = result["num_green_potions"]
    rp = result["num_red_potions"]
    bp = result["num_blue_potions"]
    if gp:
        catalog.append(
            {
                    "sku": "GREEN_POTION",
                    "name": "green potion",
                    "quantity": gp,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
        )
    if rp:
        catalog.append(
            {
                    "sku": "RED_POTION",
                    "name": "red potion",
                    "quantity": rp,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
        )
    if bp:
        catalog.append(
            {
                    "sku": "BLUE_POTION",
                    "name": "blue potion",
                    "quantity": bp,
                    "price": 70,
                    "potion_type": [0, 0, 100, 0],
                }
        )

    return catalog