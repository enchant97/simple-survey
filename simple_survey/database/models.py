from datetime import datetime

from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
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
    expires_at = DatetimeField(null=True)

    fields = ReverseRelation["Field"]
    responses = ReverseRelation["SurveyResponse"]

    @property
    def has_expired(self):
        if self.expires_at is None:
            return False
        if self.created_at >= self.expires_at:
            return False
        return True


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


class FieldOptionVote(Model):
    """
    Store when a field option is 'voted' by the user
    """
    response: ForeignKeyRelation[SurveyResponse] = ForeignKeyField(
        "models.SurveyResponse")
    option: ForeignKeyRelation[FieldOption] = ForeignKeyField(
        "models.FieldOption", "votes")


    class PydanticMeta:
        exclude = ["option"]


# init models early, so pydantic can see relationships
Tortoise.init_models([__name__], "models")

PSurvey = pydantic_model_creator(Survey)
PField = pydantic_model_creator(Field)
PFieldOption = pydantic_model_creator(FieldOption)
PSurveyResponse = pydantic_model_creator(SurveyResponse)
PFieldValue = pydantic_model_creator(FieldValue)
PFieldFieldOptionVote = pydantic_model_creator(FieldOptionVote)
