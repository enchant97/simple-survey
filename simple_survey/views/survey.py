from datetime import datetime

from quart import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from tortoise.exceptions import DoesNotExist, ValidationError
from tortoise.transactions import atomic

from ..database.models import (Field, FieldOption, FieldOptionVote, FieldValue,
                               Survey, SurveyResponse, PFields, PSurvey)
from ..types import FieldOptionTypes, FieldTypes

blueprint = Blueprint("survey", __name__)


@blueprint.get("/")
async def get_manage_surveys():
    surveys = await Survey.all()
    return await render_template("/survey/manage.html", surveys=surveys)


@blueprint.get("/new")
async def get_new_survey():
    return await render_template("/survey/new.html")


@blueprint.post("/new")
async def post_new_survey():
    try:
        form = await request.form
        title = form["title"].strip()
        description = form["description"].strip()
        closes_at = form.get("closes_at")

        if closes_at is not None and closes_at != "":
            closes_at = datetime.fromisoformat(closes_at)
        else:
            closes_at = None

        survey = await Survey.create(
            title=title,
            description=description,
            closes_at=closes_at,
        )
    except (KeyError, ValueError, ValidationError):
        await flash("Failed to create survey", "danger")
        return redirect(url_for(".get_new_survey"))
    else:
        await flash("Created survey", "success")
        return redirect(url_for(".get_survey_edit", survey_id=survey.id))


@blueprint.get("/<int:survey_id>")
async def get_survey(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        fields = await survey.fields.all().prefetch_related("options")

    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "/survey/view.html",
            survey=survey,
            fields=fields,
            FieldTypes=FieldTypes,
        )


@blueprint.post("<int:survey_id>/vote")
@atomic()
async def post_survey_vote(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        if survey.is_closed:
            await flash("Survey is closed!", "danger")
            abort(404)

        form = await request.form

        response = SurveyResponse(survey=survey)
        await response.save()

        for key, value in form.items():
            field = await survey.fields.filter(id=key).get()
            try:
                FieldOptionTypes(field.field_type.value)
                option = await field.options.filter(id=value).get()
                await FieldOptionVote.create(response=response, option=option)
            except ValueError:
                if field.field_type == FieldTypes.SHORT_TEXT:
                    await FieldValue.create(response=response, field=field, value=value.strip()[:60])
                elif field.field_type == FieldTypes.LONG_TEXT:
                    await FieldValue.create(response=response, field=field, value=value.strip()[:255])
                elif field.field_type == FieldTypes.EMAIL:
                    # TODO match email regex here
                    await FieldValue.create(response=response, field=field, value=value[:255])
                elif field.field_type == FieldTypes.PHONE:
                    # TODO match phone regex here
                    await FieldValue.create(response=response, field=field, value=value[255])
                elif field.field_type == FieldTypes.INTEGER:
                    await FieldValue.create(response=response, field=field, value=int(value))
                else:
                    abort(404)

    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_survey_thanks", survey_id=survey_id))


@blueprint.get("/<int:survey_id>/thanks")
async def get_survey_thanks(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/survey/thanks.html", survey=survey)


@blueprint.get("/<int:survey_id>/report")
async def get_survey_report(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        survey_response_count = await survey.responses.all().count()
        fields = await survey.fields.all().prefetch_related("options", "options__votes", "values")
    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "/survey/report.html",
            survey=survey,
            survey_response_count=survey_response_count,
            fields=fields,
            FieldTypes=FieldTypes,
        )


@blueprint.get("/<int:survey_id>/report.csv")
async def get_survey_report_csv(survey_id: int):
    def generate(fields: list[Field]):
        yield "Response ID, Field Caption, Field Type, Value, When\n"

        for field in fields:
            try:
                # process fields with options
                FieldOptionTypes(field.field_type.value)

                for option in field.options:
                    for vote in option.votes:
                        yield (f"{vote.response.id}, '{field.caption}', " +
                               f"{field.field_type.value},{option.caption}, " +
                               f"{vote.response.when}\n")
            except ValueError:
                # process fields with values
                for value in field.values:
                    yield (f"{value.response.id}, '{field.caption}', " +
                           f"{field.field_type.value}, '{value.value}', " +
                           f"{vote.response.when}\n")

    try:
        survey = await Survey.get(id=survey_id)
        fields = await survey.fields.all().prefetch_related(
            "options", "options__votes",
            "options__votes__response",
            "values", "values__response",
        )
    except DoesNotExist:
        abort(404)
    else:
        return current_app.response_class(generate(fields), mimetype="text/csv")


@blueprint.get("/<int:survey_id>/report.json")
async def get_survey_report_json(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        fields = await PFields.from_queryset(survey.fields.all())
    except DoesNotExist:
        abort(404)
    else:
        return fields.json()


@blueprint.get("/<int:survey_id>/report/with-meta.json")
async def get_survey_report_json_with_meta(survey_id: int):
    try:
        survey = await PSurvey.from_queryset_single(Survey.get(id=survey_id))
    except DoesNotExist:
        abort(404)
    else:
        return survey.json()


@blueprint.get("/<int:survey_id>/edit")
async def get_survey_edit(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        fields = await survey.fields.all()
    except DoesNotExist:
        abort(404)
    else:
        return await render_template("/survey/edit.html", survey=survey, fields=fields)


@blueprint.get("/<int:survey_id>/delete")
async def get_survey_delete(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        await survey.delete()
        await flash("Deleted survey", "success")
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_manage_surveys"))


@blueprint.post("/<int:survey_id>/edit")
async def post_survey_edit(survey_id: int):
    try:
        form = await request.form
        title = form["title"]
        description = form["description"]
        closes_at = form.get("closes_at")

        if closes_at is not None and closes_at != "":
            closes_at = datetime.fromisoformat(closes_at)
        else:
            closes_at = None

        survey = await Survey.get(id=survey_id)
        survey.title = title
        survey.description = description
        survey.closes_at = closes_at
        await survey.save()
    except (KeyError, ValueError, ValidationError):
        await flash("Failed to update survey", "danger")
        return redirect(url_for(".get_survey_edit", survey_id=survey_id))
    except DoesNotExist:
        abort(404)
    else:
        await flash("Updated survey", "success")
        return redirect(url_for(".get_survey_edit", survey_id=survey_id))


@blueprint.get("/<int:survey_id>/edit/field/new")
async def get_survey_field_new(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field_types = [type_.value for type_ in FieldTypes]
    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "/survey/field-new.html",
            survey=survey,
            field_types=field_types,
            add_another=request.args.get("add_another", False, bool),
        )


@blueprint.post("/<int:survey_id>/edit/field/new")
async def post_survey_field_new(survey_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        form = await request.form
        caption = form["caption"].strip()
        field_type = FieldTypes(form["field-type"])
        required = form.get("required", False, bool)

        field = await Field.create(
            survey=survey,
            caption=caption,
            field_type=field_type,
            required=required,
        )

        await flash("Created new field", "success")

        if form.get("form-add-another", False, bool):
            # allow for going back to "add new" form when mass creating
            return redirect(url_for(
                ".get_survey_field_new",
                survey_id=survey_id,
                add_another="1"
            ))

        try:
            _ = FieldOptionTypes(field_type.value)
            return redirect(url_for(
                ".get_survey_field_edit",
                survey_id=survey_id,
                field_id=field.id
            ))
        except ValueError:
            return redirect(url_for(".get_survey_edit", survey_id=survey_id))

    except KeyError:
        await flash("Failed to add new field", "danger")
        return redirect(url_for(".get_survey_field_new", survey_id=survey_id))
    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:survey_id>/edit/field/<int:field_id>/edit")
async def get_survey_field_edit(survey_id: int, field_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field: Field = await survey.fields.filter(id=field_id).get()
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
            "survey/field-edit.html",
            survey=survey,
            field=field,
            field_types=field_types,
            allow_options=allow_options,
            options=options,
        )


@blueprint.post("/<int:survey_id>/edit/field/<int:field_id>/edit")
async def post_survey_field_edit(survey_id: int, field_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field = await survey.fields.filter(id=field_id).get()

        form = await request.form

        field.caption = form["caption"].strip()
        field.field_type = FieldTypes(form["field-type"])
        field.required = form.get("required", False, bool)

        await field.save()

        await flash("Updated field", "success")
        return redirect(url_for(".get_survey_edit", survey_id=survey_id))

    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:survey_id>/edit/field/<int:field_id>/delete")
async def get_survey_field_delete(survey_id: int, field_id: int):
    try:
        field = await Field.get(id=field_id)
        await field.delete()
        await flash("Deleted field", "success")
    except DoesNotExist:
        abort(404)
    else:
        return redirect(url_for(".get_survey_edit", survey_id=survey_id))


@blueprint.get("/<int:survey_id>/edit/field/<int:field_id>/new-option")
async def get_survey_field_new_option(survey_id: int, field_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field = await survey.fields.filter(id=field_id).get()

    except DoesNotExist:
        abort(404)
    else:
        return await render_template(
            "survey/option-new.html",
            survey=survey,
            field=field,
            add_another=request.args.get("add_another", False, bool),
        )


@blueprint.post("/<int:survey_id>/edit/field/<int:field_id>/new-option")
async def post_survey_field_new_option(survey_id: int, field_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field = await survey.fields.filter(id=field_id).get()

        form = await request.form
        caption = form["caption"].strip()

        await FieldOption.create(field=field, caption=caption)

        await flash("Created new field option", "success")

        if form.get("form-add-another", False, bool):
            # allow for going back to "add new" form when mass creating
            return redirect(url_for(
                ".get_survey_field_new_option",
                survey_id=survey_id,
                field_id=field_id,
                add_another="1"
            ))

        return redirect(url_for(
            "survey.get_survey_field_edit",
            survey_id=survey.id,
            field_id=field.id
        ))

    except DoesNotExist:
        abort(404)


@blueprint.get("/<int:survey_id>/edit/field/<int:field_id>/<int:option_id>/delete")
async def get_survey_field_option_delete(survey_id: int, field_id: int, option_id: int):
    try:
        survey = await Survey.get(id=survey_id)
        field: Field = await survey.fields.filter(id=field_id).get()
        await field.options.filter(id=option_id).delete()

        await flash("Deleted field option", "success")
        return redirect(url_for('survey.get_survey_field_edit', survey_id=survey.id, field_id=field.id))

    except DoesNotExist:
        abort(404)
