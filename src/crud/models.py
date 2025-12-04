from tortoise import fields
from tortoise.models import Model

from crud.enums import InstitutueEnum, RoleEnum


class Admin(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(unique=True, max_length=100, null=True)
    telegram_id = fields.IntField(unique=True, null=False)
    role = fields.CharEnumField(enum_type=RoleEnum, null=False)


class Visitor(Model):
    id = fields.IntField(pk=True)
    full_name = fields.CharField(null=False)
    program = fields.CharEnumField(enum_type=InstitutueEnum, null=True)
    grade = fields.CharField(null=False)
    phone = fields.CharField(null=True, unique=False)
    email = fields.CharField(null=True, unique=True)
