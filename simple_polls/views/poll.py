from quart import Blueprint, redirect, render_template, url_for

blueprint = Blueprint("poll", __name__)


@blueprint.get("/")
async def get_manage_polls():
    return await render_template("/poll/manage.html")


@blueprint.get("/new")
async def get_new_poll():
    return await render_template("/poll/new.html")


@blueprint.post("/new")
async def post_new_poll():
    return redirect(url_for(".get_manage_polls"))


@blueprint.get("/<int:poll_id>")
async def get_poll(poll_id: int):
    return await render_template("/poll/view.html")


@blueprint.get("/<int:poll_id>/edit")
async def get_poll_edit(poll_id: int):
    return await render_template("/poll/edit.html")


@blueprint.post("/<int:poll_id>/edit")
async def post_poll_edit(poll_id: int):
    return redirect(url_for(".get_poll", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/delete")
async def get_poll_delete(poll_id: int):
    return redirect(url_for(".get_manage_polls"))
