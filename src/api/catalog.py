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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions WHERE inventory > 0 LIMIT 6")).mappings()
        result = result.fetchall()
        
    catalog = []

    for potion in result:
        type = [potion["red_amt"], potion["green_amt"], potion["blue_amt"], potion["dark_amt"]]
        catalog.append(
            {
                "sku": potion["sku"],
                "name": potion["sku"],
                "quantity": potion["inventory"],
                "price": potion["price"],
                "potion_type": type
            }
        )

    print ("Catalog: ", catalog)

    return catalog