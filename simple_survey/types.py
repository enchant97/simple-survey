from enum import Enum


class FieldOptionTypes(Enum):
    RADIO = "radio"
    CHECK = "check"
    DROP_DOWN = "drop-down"


class FieldValueTypes(Enum):
    SHORT_TEXT = "short-text"
    LONG_TEXT = "long-text"
    EMAIL = "email"
    PHONE = "phone"
    INTEGER = "integer"


class FieldTypes(Enum):
    RADIO = "radio"
    CHECK = "check"
    DROP_DOWN = "drop-down"

    SHORT_TEXT = "short-text"
    LONG_TEXT = "long-text"
    EMAIL = "email"
    PHONE = "phone"
    INTEGER = "integer"
