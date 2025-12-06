import re
from pydantic import BaseModel, field_validator

from crud.enums import InstitutueEnum

PHONE_PATTERN = re.compile(r'^\+7\s9\d{2}\s\d{3}-\d{2}-\d{2}$')
EMAIL_PATTERN = re.compile(
    r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$'
)


class VisitorSchema(BaseModel):
    id: int
    full_name: str
    program: InstitutueEnum
    grade: str
    phone: str
    email: str

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str):
        if not PHONE_PATTERN.full_match(v):
            raise ValueError('телефон не соответствует формату: "+7 999 123-45-67"')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.fullmatch(v):
            raise ValueError('почта не соотвествует формату: "user@example.com"')
        return v
