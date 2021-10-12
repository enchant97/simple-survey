from datetime import datetime

from quart import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from tortoise.exceptions import DoesNotExist, ValidationError

from ..database.models import Choice, PChoice, PQuestion, Question, Vote

blueprint = Blueprint("poll", __name__)


@blueprint.get("/")
async def get_manage_polls():
    polls = await Question.all()
    return await render_template("/poll/manage.html", polls=polls)


@blueprint.get("/new")
async def get_new_poll():
    return await render_template("/poll/new.html")


@blueprint.post("/new")
async def post_new_poll():
    try:
        form = await request.form
        title = form["title"]
        description = form["description"]
        expires_at = form.get("expires_at")

        if expires_at is not None and expires_at != "":
            expires_at = datetime.fromisoformat(expires_at)
            if expires_at < datetime.now():
                raise ValueError()
        else:
            expires_at = None

        question = await Question.create(
            title=title,
            description=description,
            expires_at=expires_at,
        )
    except (KeyError, ValueError, ValidationError):
        await flash("Failed to create poll", "error")
        return redirect(url_for(".get_new_poll"))
    else:
        await flash("Created poll")
        return redirect(url_for(".get_poll_edit", poll_id=question.id))


@blueprint.get("/<int:poll_id>")
async def get_poll(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        choices = await poll.choices.all()
        # TODO check if poll is expired
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/view.html", poll=poll, choices=choices)


@blueprint.post("<int:poll_id>/vote")
async def post_poll_vote(poll_id: int):
    try:
        # TODO check if poll is expired
        poll = await Question.get(id=poll_id)
        form = await request.form
        choice_id = int(form["poll-choice"])

        choice = await Choice.get_or_none(id=choice_id)
        if choice is None:
            raise KeyError()

        await Vote.create(choice=choice)

    except (KeyError, ValueError):
        await flash("Failed to cast vote", "error")
        return redirect(url_for(".get_poll", poll_id=poll_id))
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_poll_thanks", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/thanks")
async def get_poll_thanks(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/thanks.html", poll=poll)


@blueprint.get("/<int:poll_id>/report")
async def get_poll_report(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        choices = await poll.choices.all()
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/report.html", poll=poll, choices=choices)


@blueprint.get("/<int:poll_id>/report.csv")
async def get_poll_report_csv(poll_id: int):
    def generate(choices: list[Choice]):
        yield "Caption, Votes\n"
        for choice in choices:
            caption = choice.caption
            votes = len(choice.votes)
            yield f"'{caption}', {votes}\n"
    try:
        poll = await Question.get(id=poll_id)
        choices = await poll.choices.all().prefetch_related("votes")
    except DoesNotExist:
        abort(404)
    else:
        return current_app.response_class(generate(choices), mimetype="text/csv")


@blueprint.get("/<int:poll_id>/report.json")
async def get_poll_report_json(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        choices = [choice.dict() for choice in await PChoice.from_queryset(poll.choices.all())]
    except DoesNotExist:
        abort(404)
    else:
        return jsonify(choices)


@blueprint.get("/<int:poll_id>/report/with-meta.json")
async def get_poll_report_json_with_meta(poll_id: int):
    try:
        choices = (await PQuestion.from_queryset_single(Question.get(id=poll_id))).dict()
    except DoesNotExist:
        abort(404)
    else:
        return jsonify(choices)


@blueprint.get("/<int:poll_id>/edit")
async def get_poll_edit(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        choices = await poll.choices.all()
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/edit.html", poll=poll, choices=choices)


@blueprint.post("/<int:poll_id>/edit")
async def post_poll_edit(poll_id: int):
    try:
        form = await request.form
        title = form["title"]
        description = form["description"]
        expires_at = form.get("expires_at")

        if expires_at is not None and expires_at != "":
            expires_at = datetime.fromisoformat(expires_at)
            if expires_at < datetime.now():
                raise ValueError()
        else:
            expires_at = None

        poll = await Question.get(id=poll_id)
        poll.title = title
        poll.description = description
        poll.expires_at = expires_at
        await poll.save()
    except (KeyError, ValueError, ValidationError):
        await flash("Failed to update poll", "error")
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))
    except DoesNotExist:
        abort(404)
    else:
        await flash("Updated poll")
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/delete")
async def get_poll_delete(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        await poll.delete()
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_manage_polls"))


@blueprint.post("/<int:poll_id>/choices/new")
async def post_manage_choices_new(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        form = await request.form
        await Choice.create(
            question=poll,
            caption=form["caption"],
        )
    except (KeyError, ValidationError):
        await flash("Failed to update poll", "error")
        return redirect(url_for("get_poll_edit", poll_id=poll_id))
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/choices/<int:choice_id>/delete")
async def get_manage_choices_delete(poll_id: int, choice_id: int):
    try:
        choice = await Choice.get(id=choice_id)
        await choice.delete()
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))
