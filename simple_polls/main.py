from quart import Quart
from tortoise.contrib.quart import register_tortoise

from .config import get_settings
from .database import models

app = Quart(__name__)


def create_app():
    app.secret_key = get_settings().SECRET_KEY
    # database setup
    register_tortoise(
        app,
        db_url=get_settings().DB_URI,
        modules={"models": [models]},
        generate_schemas=True)
    return app
