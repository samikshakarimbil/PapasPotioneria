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
        potions = connection.execute(sqlalchemy.text("""SELECT * FROM potions""")).mappings().fetchall()
        
    catalog = []
    potion_dict = {}

    for potion in potions:
        type = [potion["red_amt"], potion["green_amt"], potion["blue_amt"], potion["dark_amt"]]
        sku =  potion["sku"]
        quantity = potion["inventory"]
        if sku in potion_dict:
            qty = int(potion_dict[sku]["quantity"])
            qty += quantity
            potion_dict[sku]["quantity"] = qty
        else:
            potion_dict[sku] = {
            "sku": potion["sku"],
            "name": potion["sku"],
            "quantity": potion["inventory"],
            "price": potion["price"],
            "potion_type": type
        }
            
    print(f"Potion dict: {potion_dict}")

    catalog = list(potion_dict.values())
    for potion in catalog:
        if potion["quantity"] == 0:
            catalog.remove(potion)

    if len(catalog) > 6:
        catalog = catalog[:6]

    print ("Catalog: ", catalog)
    return catalog