from datetime import datetime

from tortoise import Tortoise, timezone
from tortoise.contrib.pydantic import (pydantic_model_creator,
                                       pydantic_queryset_creator)
from tortoise.fields import (BooleanField, CharEnumField, CharField,
                             DatetimeField, ForeignKeyField,
                             ForeignKeyRelation, IntField, ReverseRelation)
from tortoise.models import Model

from ..types import FieldTypes


class Survey(Model):
    """
    Information related to a created survey
    """
    title = CharField(max_length=100)
    description = CharField(max_length=200)
    created_at = DatetimeField(auto_now_add=True)
    closes_at = DatetimeField(null=True)

    fields = ReverseRelation["Field"]
    responses = ReverseRelation["SurveyResponse"]

    @property
    def closes_at_as_html_input_value(self) -> str:
        if self.closes_at:
            return self.closes_at.strftime("%Y-%m-%dT%H:%M")
        return None

    @property
    def is_closed(self) -> bool:
        if self.closes_at is None:
            return False
        if timezone.now() <= self.closes_at:
            return False
        return True

    class PydanticMeta:
        exclude = ["responses"]


class Field(Model):
    """
    A survey's field (either a group of options or a value)
    """
    survey: ForeignKeyRelation[Survey] = ForeignKeyField(
        "models.Survey", "fields")
    caption = CharField(max_length=200)
    field_type = CharEnumField(FieldTypes)
    required = BooleanField(default=True)

    values = ReverseRelation["FieldValue"]
    options = ReverseRelation["FieldOption"]

    class PydanticMeta:
        exclude = ["survey"]


class FieldOption(Model):
    """
    A field option to group multiple
    possible options for a single field
    """
    field: ForeignKeyRelation[Field] = ForeignKeyField(
        "models.Field", "options")
    caption = CharField(max_length=200)

    votes = ReverseRelation["FieldOptionVote"]

    class PydanticMeta:
        exclude = ["field"]


class SurveyResponse(Model):
    """
    When a user has submitted a survey response,
    used to group together survey field responses
    """
    survey: ForeignKeyRelation[Survey] = ForeignKeyField(
        "models.Survey", "responses")
    when = DatetimeField(auto_now_add=True)

    class PydanticMeta:
        exclude = ["survey"]


class FieldValue(Model):
    """
    A value stored relating to a
    field (the users entered value)
    """
    response: ForeignKeyRelation[SurveyResponse] = ForeignKeyField(
        "models.SurveyResponse")
    field: ForeignKeyRelation[Field] = ForeignKeyField(
        "models.Field", "values")
    value = CharField(255)

    class PydanticMeta:
        exclude = ["response", "field"]


class FieldOptionVote(Model):
    """
    Store when a field option is 'voted' by the user
    """
    response: ForeignKeyRelation[SurveyResponse] = ForeignKeyField(
        "models.SurveyResponse")
    option: ForeignKeyRelation[FieldOption] = ForeignKeyField(
        "models.FieldOption", "votes")


    class PydanticMeta:
        exclude = ["response", "option"]


# init models early, so pydantic can see relationships
Tortoise.init_models([__name__], "models")

PSurvey = pydantic_model_creator(Survey)
PFields = pydantic_queryset_creator(Field)
