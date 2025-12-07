import asyncio
import json as std_json
from pathlib import Path
from typing import Any, Dict, List, Optional

from settings import Settings


settings = Settings()


def _get_members_file_path() -> Path:
    return Path(settings._BASE_DIR).parent / settings.members_json_name


async def _load_members() -> List[Dict[str, Any]]:
    path = _get_members_file_path()

    def _read() -> List[Dict[str, Any]]:
        with path.open('r', encoding='utf-8') as f:
            return std_json.load(f)

    return await asyncio.to_thread(_read)


async def check(
    full_name: Optional[str] = None, phone: Optional[str] = None
) -> List[Dict[str, Any]]:
    data = await _load_members()
    result: List[Dict[str, Any]] = []
    q_name = full_name.strip().lower() if full_name else None
    q_phone = ''.join(ch for ch in phone if ch.isdigit()) if phone else None
    for item in data:
        name = item.get('ФИО')
        phone_value = item.get('Номер телефона')
        if q_name is not None:
            if not isinstance(name, str):
                continue
            if q_name != name.strip().lower():
                continue
        if q_phone is not None:
            if not isinstance(phone_value, str):
                continue
            digits = ''.join(ch for ch in phone_value if ch.isdigit())
            if q_phone != digits:
                continue
        result.append(item)
    return result
