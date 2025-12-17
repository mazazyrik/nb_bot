import asyncio
import random
from pathlib import Path
from typing import Any, Optional, Tuple

import aiohttp

from settings import Settings


settings = Settings()

IAM_URL = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
GPT_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

_iam_token: Optional[str] = None

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=35, connect=10, sock_read=25)
_RETRY_ATTEMPTS = 5
_RETRY_BASE_DELAY_SEC = 0.6
_RETRY_MAX_DELAY_SEC = 6.0

_system_prompt_path = Path(__file__).resolve().parent.parent / 'SYSTEM_PROMPT.md'
with _system_prompt_path.open('r', encoding='utf-8') as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()


def _retry_delay(attempt: int) -> float:
    base = min(_RETRY_BASE_DELAY_SEC * (2**attempt), _RETRY_MAX_DELAY_SEC)
    return base + random.uniform(0.0, base * 0.2)


async def _post_json_with_retries(
    url: str, payload: Any, headers: Optional[dict] = None
) -> Tuple[int, Any]:
    last_error: Optional[BaseException] = None
    async with aiohttp.ClientSession(timeout=_REQUEST_TIMEOUT) as session:
        for attempt in range(_RETRY_ATTEMPTS):
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        data = await response.text()

                    status = response.status
                    if status == 429 or 500 <= status < 600:
                        last_error = RuntimeError(f'bad status {status}: {data}')
                    else:
                        return status, data
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e

            if attempt < _RETRY_ATTEMPTS - 1:
                await asyncio.sleep(_retry_delay(attempt))

    raise RuntimeError('request failed') from last_error


async def _get_iam_token() -> str:
    global _iam_token
    if _iam_token:
        return _iam_token

    status, data = await _post_json_with_retries(
        IAM_URL,
        payload={'yandexPassportOauthToken': settings.yandex_gpt_oauth_token},
    )
    if status != 200 or not isinstance(data, dict):
        raise RuntimeError(f'cannot get iam token: {status} {data}')

    token = data.get('iamToken')
    if not token:
        raise RuntimeError(f'cannot get iam token: {data}')

    _iam_token = token
    return token


async def get_completion(name: str) -> Optional[str]:
    system_text = (
        SYSTEM_PROMPT_TEMPLATE
        + '\n\n'
        + f'Имя пользователя: {name}. Обращайся к пользователю по имени {name} '
        + 'и обязательно используй это имя в пожелании.'
    )

    payload = {
        'modelUri': f'gpt://{settings.yandex_gpt_folder_id}/yandexgpt-lite',
        'completionOptions': {
            'stream': False,
            'temperature': 0.3,
            'maxTokens': '2000',
        },
        'messages': [
            {
                'role': 'system',
                'text': system_text,
            },
            {
                'role': 'user',
                'text': 'Сгенерируй пожелание.',
            },
        ],
    }

    global _iam_token
    for _ in range(2):
        iam_token = await _get_iam_token()
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json',
        }

        status, data = await _post_json_with_retries(
            GPT_URL,
            payload=payload,
            headers=headers,
        )
        if status == 401 and _iam_token:
            _iam_token = None
            continue

        if status != 200 or not isinstance(data, dict):
            raise RuntimeError(f'gpt request failed: {status} {data}')

        result = data.get('result') or {}
        alternatives = result.get('alternatives') or []
        if not alternatives:
            return None
        message = alternatives[0].get('message') or {}
        return message.get('text')

    return None
