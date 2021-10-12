from datetime import datetime

from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.fields import (CharField, DatetimeField, ForeignKeyField,
                             ForeignKeyRelation, IntField, ReverseRelation)
from tortoise.models import Model


class Question(Model):
    title = CharField(max_length=100)
    description = CharField(max_length=200)
    created_at = DatetimeField(auto_now_add=True)
    expires_at = DatetimeField(null=True)

    choices = ReverseRelation["Choice"]

    @property
    def has_expired(self):
        if self.expires_at is None:
            return False
        if self.created_at >= self.expires_at:
            return False
        return True


class Choice(Model):
    question: ForeignKeyRelation[Question] = ForeignKeyField(
        "models.Question", "choices")
    caption = CharField(max_length=200)
    votes = ReverseRelation["Vote"]

    class PydanticMeta:
        exclude = ["question"]


class Vote(Model):
    choice: ForeignKeyRelation[Choice] = ForeignKeyField(
        "models.Choice", "votes")
    when = DatetimeField(auto_now_add=True)

    class PydanticMeta:
        exclude = ["choice"]


# init models early, so pydantic can see relationships
Tortoise.init_models([__name__], "models")

PQuestion = pydantic_model_creator(Question)
PChoice = pydantic_model_creator(Choice)
PVote = pydantic_model_creator(Vote)
