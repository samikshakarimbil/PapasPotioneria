from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE from global_inventory"))
        connection.execute(sqlalchemy.text("""INSERT INTO global_inventory(gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, transaction)
                                           VALUES(100, 0, 0, 0, 0 'Shop reset')"""))
        connection.execute(sqlalchemy.text("DELETE from cart_items"))
        connection.execute(sqlalchemy.text("DELETE from carts"))
        connection.execute(sqlalchemy.text("DELETE from potions"))
    return "OK"

