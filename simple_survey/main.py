from quart import Quart
from tortoise.contrib.quart import register_tortoise

from .config import get_settings
from .database import models
from .views import home, survey

app = Quart(__name__)


def create_app():
    app.secret_key = get_settings().SECRET_KEY
    app.config["TITLE_NAME"] = get_settings().TITLE_NAME
    # register routes
    app.register_blueprint(home.blueprint, url_prefix="/")
    app.register_blueprint(survey.blueprint, url_prefix="/surveys")
    # database setup
    register_tortoise(
        app,
        db_url=get_settings().DB_URI,
        modules={"models": [models]},
        generate_schemas=True)
    return app
