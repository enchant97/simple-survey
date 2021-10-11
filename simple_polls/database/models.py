
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
    votes = IntField(default=0)

    def as_dict(self):
        return {
            "caption": self.caption,
            "votes": self.votes,
        }
