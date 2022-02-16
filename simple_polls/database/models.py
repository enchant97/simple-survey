from datetime import datetime

from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.fields import (BooleanField, CharEnumField, CharField,
                             DatetimeField, ForeignKeyField,
                             ForeignKeyRelation, IntField, ReverseRelation)
from tortoise.models import Model

from ..types import FieldTypes


class Poll(Model):
    """
    Information related to a created poll
    """
    title = CharField(max_length=100)
    description = CharField(max_length=200)
    created_at = DatetimeField(auto_now_add=True)
    expires_at = DatetimeField(null=True)

    fields = ReverseRelation["Field"]

    @property
    def has_expired(self):
        if self.expires_at is None:
            return False
        if self.created_at >= self.expires_at:
            return False
        return True


class Field(Model):
    """
    A poll's field (either a group of options or a value)
    """
    poll: ForeignKeyRelation[Poll] = ForeignKeyField(
        "models.Poll", "fields")
    caption = CharField(max_length=200)
    field_type = CharEnumField(FieldTypes)
    required = BooleanField(default=True)

    values = ReverseRelation["FieldValue"]
    options = ReverseRelation["FieldOption"]

    class PydanticMeta:
        exclude = ["poll"]


class FieldValue(Model):
    """
    A value stored relating to a
    field (the users entered value)
    """
    field: ForeignKeyRelation[Field] = ForeignKeyField(
        "models.Field", "values")
    when = DatetimeField(auto_now_add=True)
    value = CharField(255)


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


class FieldOptionVote(Model):
    """
    Store when a field option is 'voted' by the user
    """
    option: ForeignKeyRelation[FieldOption] = ForeignKeyField(
        "models.FieldOption", "votes")
    when = DatetimeField(auto_now_add=True)


    class PydanticMeta:
        exclude = ["option"]


# init models early, so pydantic can see relationships
Tortoise.init_models([__name__], "models")

PPoll = pydantic_model_creator(Poll)
PField = pydantic_model_creator(Field)
PFieldValue = pydantic_model_creator(FieldValue)
PFieldOption = pydantic_model_creator(FieldOption)
PFieldFieldOptionVote = pydantic_model_creator(FieldOptionVote)
