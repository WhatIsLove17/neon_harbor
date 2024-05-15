import app.database.requests as requests
from app.core.entities_service import get_places_count

async def add_promo(name, desc):

    names = name.replace(' ', '').split('\n')
    await requests.add_promo(names=names, description=desc)

async def use_promo(name):
    return await requests.use_promo(name=name)