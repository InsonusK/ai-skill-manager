"""Frontmatter split/join helpers.

Вспомогательные функции для разбиения и сборки frontmatter.
"""

from typing import Any, Optional, Tuple

import yaml


def split(content: str) -> Tuple[Optional[dict[str, Any]], str]:
    """Split markdown content into (frontmatter_dict, body).

    Разбивает markdown-содержимое на (словарь frontmatter, тело).

    Returns ``(None, content)`` if no valid ``---`` frontmatter block is found,
    so the original content is never lost.

    Возвращает ``(None, content)``, если корректный блок frontmatter ``---``
    не найден, чтобы исходное содержимое никогда не терялось.
    """
    if not content.startswith("---"):
        return None, content

    rest = content[3:]
    end_idx = rest.find("---")
    if end_idx == -1:
        return None, content

    frontmatter_text = rest[:end_idx].strip()
    if not frontmatter_text:
        return None, content

    body = rest[end_idx + 3:]
    if body.startswith("\n"):
        body = body[1:]

    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None, content

    if not isinstance(parsed, dict):
        return None, content

    return parsed, body


def join(frontmatter: dict[str, Any], body: str) -> str:
    """Serialize a frontmatter dict and a body back into markdown content.

    Сериализует словарь frontmatter и тело обратно в markdown-содержимое.
    """
    frontmatter_text = yaml.safe_dump(
        frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{frontmatter_text}\n---\n{body}"
