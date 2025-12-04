from crud.exceptions import AdminNotFound
from crud.models import Admin, Visitor
from schemas.visitor import VisitorSchema


async def get_visitor_or_none(phone: str):
    visitor = Visitor.get_or_none(
        phone=phone
    )
    return VisitorSchema(
        *visitor
    )


async def check_admin(telegram_id: int):
    user = await Admin.get_or_none(
        telegram_id=telegram_id
    )
    if not user:
        raise AdminNotFound(telegram_id)
