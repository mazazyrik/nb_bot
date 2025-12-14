import uuid

from tortoise import fields
from tortoise.models import Model

from crud.enums import InstitutueEnum, RoleEnum


class Admin(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(unique=True, max_length=100, null=True)
    telegram_id = fields.BigIntField(unique=True, null=False)
    role = fields.CharEnumField(enum_type=RoleEnum, null=False)


class Visitor(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, null=False)
    telegram_username = fields.CharField(
        max_length=64, null=True, unique=False, index=True
    )
    full_name = fields.CharField(max_length=100, null=False)
    program = fields.CharEnumField(enum_type=InstitutueEnum, null=True)
    grade = fields.CharField(max_length=100, null=False)
    phone = fields.CharField(max_length=100, null=True, unique=False)
    email = fields.CharField(max_length=100, null=True, unique=True)
    whish = fields.TextField(null=True)


class LookRequest(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    visitor_telegram_id = fields.BigIntField(null=False, index=True)
    photo_file_id = fields.CharField(max_length=512, null=False)
    status = fields.CharField(max_length=32, null=False, default='pending')
