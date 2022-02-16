from datetime import datetime

from quart import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from tortoise.exceptions import DoesNotExist, ValidationError

from ..database.models import Field, FieldOption, Poll
from ..types import FieldOptionTypes, FieldTypes, FieldValueTypes

blueprint = Blueprint("poll", __name__)


@blueprint.get("/")
async def get_manage_polls():
    polls = await Poll.all()
    return await render_template("/poll/manage.html", polls=polls)


@blueprint.get("/new")
async def get_new_poll():
    return await render_template("/poll/new.html")


@blueprint.post("/new")
async def post_new_poll():
    try:
        form = await request.form
        title = form["title"].strip()
        description = form["description"].strip()
        expires_at = form.get("expires_at")

        if expires_at is not None and expires_at != "":
            expires_at = datetime.fromisoformat(expires_at)
            if expires_at < datetime.now():
                await flash("Failed to create poll as 'expiry' is in the past", "danger")
                return redirect(url_for(".get_new_poll"))
        else:
            expires_at = None

        poll = await Poll.create(
            title=title,
            description=description,
            expires_at=expires_at,
        )
    except (KeyError, ValueError, ValidationError):
        await flash("Failed to create poll", "danger")
        return redirect(url_for(".get_new_poll"))
    else:
        await flash("Created poll", "success")
        return redirect(url_for(".get_poll_edit", poll_id=poll.id))


@blueprint.get("/<int:poll_id>")
async def get_poll(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        if poll.has_expired:
            await poll.delete()
            await flash("poll has expired!", "danger")
            abort(404)
        choices = await poll.choices.all()
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/view.html", poll=poll, choices=choices)


@blueprint.post("<int:poll_id>/vote")
async def post_poll_vote(poll_id: int):
    try:
        poll = await Question.get(id=poll_id)
        if poll.has_expired:
            await poll.delete()
            await flash("poll has expired!", "danger")
            abort(404)
        form = await request.form
        choice_id = int(form["poll-choice"])

        choice = await Choice.get_or_none(id=choice_id)
        if choice is None:
            raise KeyError()

        await Vote.create(choice=choice)

    except (KeyError, ValueError):
        await flash("Failed to cast vote", "danger")
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
        poll = await Poll.get(id=poll_id)
        fields = await poll.fields.all()
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/poll/edit.html", poll=poll, fields=fields)


@blueprint.get("/<int:poll_id>/delete")
async def get_poll_delete(poll_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        await poll.delete()
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_manage_polls"))


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
        await flash("Failed to update poll", "danger")
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))
    except DoesNotExist:
        abort(404)
    else:
        await flash("Updated poll", "success")
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/edit/field/new")
async def get_poll_field_new(poll_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field_types = [type_.value for type_ in FieldTypes]
    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "/poll/field-new.html",
            poll=poll,
            field_types=field_types
        )


@blueprint.post("/<int:poll_id>/edit/field/new")
async def post_poll_field_new(poll_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        form = await request.form
        caption = form["caption"].strip()
        field_type = FieldTypes(form["field-type"])
        required = form.get("required", False, bool)

        field = await Field.create(
            poll=poll,
            caption=caption,
            field_type=field_type,
            required=required,
        )

        try:
            _ = FieldOptionTypes(field_type.value)
            return redirect(url_for(
                ".get_poll_field_edit",
                poll_id=poll_id,
                field_id=field.id
            ))
        except ValueError:
            return redirect(url_for(".get_poll_edit", poll_id=poll_id))

    except KeyError:
        await flash("Failed to add new field", "danger")
        return redirect(url_for(".get_poll_field_new", poll_id=poll_id))
    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:poll_id>/edit/field/<int:field_id>/edit")
async def get_poll_field_edit(poll_id: int, field_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field: Field = await poll.fields.filter(id=field_id).get()
        field_types = [type_.value for type_ in FieldTypes]

        try:
            _ = FieldOptionTypes(field.field_type.value)
            allow_options = True
            options = await field.options.all()
        except:
            allow_options = False
            options = None

    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "poll/field-edit.html",
            poll=poll,
            field=field,
            field_types=field_types,
            allow_options=allow_options,
            options=options,
        )


@blueprint.post("/<int:poll_id>/edit/field/<int:field_id>/edit")
async def post_poll_field_edit(poll_id: int, field_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field = await poll.fields.filter(id=field_id).get()

        form = await request.form

        field.caption = form["caption"].strip()
        field.field_type = FieldTypes(form["field-type"])
        field.required = form.get("required", False, bool)

        await field.save()

        return redirect(url_for(".get_poll_edit", poll_id=poll_id))

    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:poll_id>/edit/field/<int:field_id>/delete")
async def get_poll_field_delete(poll_id: int, field_id: int):
    try:
        field = await Field.get(id=field_id)
        await field.delete()
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_poll_edit", poll_id=poll_id))


@blueprint.get("/<int:poll_id>/edit/field/<int:field_id>/new-option")
async def get_poll_field_new_option(poll_id: int, field_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field = await poll.fields.filter(id=field_id).get()

    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "poll/option-new.html",
            poll=poll,
            field=field,
        )


@blueprint.post("/<int:poll_id>/edit/field/<int:field_id>/new-option")
async def post_poll_field_new_option(poll_id: int, field_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field = await poll.fields.filter(id=field_id).get()

        caption = (await request.form)["caption"].strip()

        await FieldOption.create(field=field, caption=caption)

        return redirect(url_for('poll.get_poll_field_edit', poll_id=poll.id, field_id=field.id))

    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:poll_id>/edit/field/<int:field_id>/<int:option_id>/delete")
async def get_poll_field_option_delete(poll_id: int, field_id: int, option_id: int):
    try:
        poll = await Poll.get(id=poll_id)
        field: Field = await poll.fields.filter(id=field_id).get()
        await field.options.filter(id=option_id).delete()

        await flash("deleted field option", "success")
        return redirect(url_for('poll.get_poll_field_edit', poll_id=poll.id, field_id=field.id))

    except DoesNotExist:
        abort(404)
