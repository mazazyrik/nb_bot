from crud.exceptions import AdminNotFound
from crud.models import Admin, Visitor
from schemas.visitor import VisitorSchema


async def get_visitor_or_none(phone: str):
    visitor = await Visitor.get_or_none(phone=phone)
    if visitor is None:
        return None
    return VisitorSchema(
        id=visitor.id,
        full_name=visitor.full_name,
        program=visitor.program,
        grade=visitor.grade,
        phone=visitor.phone,
        email=visitor.email,
    )


async def check_admin(telegram_id: int):
    user = await Admin.get_or_none(telegram_id=telegram_id)
    if not user:
        raise AdminNotFound(telegram_id)


async def get_visitor_name(telegram_id: int) -> str | None:
    visitor = await Visitor.get_or_none(telegram_id=telegram_id)
    if visitor is None:
        return None
    return visitor.full_name


async def get_whish(telegram_id: int) -> str | None:
    visitor = await Visitor.get_or_none(telegram_id=telegram_id)
    if visitor is None:
        return None
    return visitor.whish
