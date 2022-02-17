from quart import Blueprint, render_template

blueprint = Blueprint("home", __name__)


@blueprint.get("/")
async def index():
    return await render_template("/home/index.html")
