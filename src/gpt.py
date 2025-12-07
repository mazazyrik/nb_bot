import asyncio
from pathlib import Path
from typing import Optional

import aiohttp

from settings import Settings


settings = Settings()

IAM_URL = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
GPT_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

_iam_token: Optional[str] = None

_system_prompt_path = Path(__file__).resolve().parent.parent / 'SYSTEM_PROMPT.md'
with _system_prompt_path.open('r', encoding='utf-8') as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()


async def _get_iam_token() -> str:
    global _iam_token
    if _iam_token:
        return _iam_token

    async with aiohttp.ClientSession() as session:
        async with session.post(
            IAM_URL,
            json={'yandexPassportOauthToken': settings.yandex_gpt_oauth_token},
        ) as response:
            data = await response.json()
            token = data.get('iamToken')
            if not token:
                raise RuntimeError(f'cannot get iam token: {data}')
            _iam_token = token
            return token


async def get_completion(name: str) -> Optional[str]:
    iam_token = await _get_iam_token()
    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json',
    }

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

    async with aiohttp.ClientSession() as session:
        async with session.post(
            GPT_URL,
            headers=headers,
            json=payload,
        ) as response:
            data = await response.json()
            result = data.get('result') or {}
            alternatives = result.get('alternatives') or []
            if not alternatives:
                return None
            message = alternatives[0].get('message') or {}
            return message.get('text')


if __name__ == '__main__':
    print(asyncio.run(get_completion('Никита')))
