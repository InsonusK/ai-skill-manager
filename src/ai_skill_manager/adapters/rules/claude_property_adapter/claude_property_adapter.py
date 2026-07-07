"""Adapter that reshapes frontmatter into Claude Code's native fields.

Адаптер, приводящий frontmatter к полям, нативно понимаемым Claude Code.
"""

from __future__ import annotations

import logging

import yaml

from ....entities import Skill
from ....entities import frontmatter as frontmatter_module
from ...models.adapter_message import AdapterMessage
from ..abs_adapter import absAdapter

logger = logging.getLogger(__name__)

# Frontmatter fields natively understood by Claude Code.
# Поля frontmatter, нативно понимаемые Claude Code.
NATIVE_FIELDS = {
    "name",
    "description",
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
}


class ClaudePropertyAdapter(absAdapter):
    """Moves non-native frontmatter fields into the file body.

    Переносит нестандартные поля frontmatter в тело файла.
    """

    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection.

        Версия адаптера для обнаружения изменений.
        """
        return "1.0.0"

    def adapt(self, old_skill: Skill, new_skill: Skill) -> AdapterMessage:
        """Reshape ``new_skill``'s frontmatter into Claude Code's native fields.

        Приводит frontmatter ``new_skill`` к нативным полям Claude Code.

        Args:
            old_skill: Original skill before copying.
                / Исходный навык до копирования.
            new_skill: Copied skill in the target directory.
                / Скопированный навык в целевой директории.

        Returns:
            Message summarizing how many fields were adapted.
                / Сообщение с количеством адаптированных полей.
        """
        file_path = new_skill.file_path
        content = file_path.read_text(encoding="utf-8")
        parsed, body = frontmatter_module.split(content)

        if parsed is None:
            return AdapterMessage(
                message="Adapted {count} frontmatter field(s)",
                params={"count": 0},
            )

        fm = dict(parsed)
        leftover: dict = {}
        moved_count = 0

        when_to_use_value = fm.pop("whenToUse", None)
        if when_to_use_value is not None:
            if isinstance(when_to_use_value, list):
                when_to_use_value = ",".join(str(v) for v in when_to_use_value)

            if "when_to_use" not in fm:
                fm["when_to_use"] = when_to_use_value
                moved_count += 1
            else:
                logger.warning(
                    "Skill %s has both 'whenToUse' and 'when_to_use' in "
                    "frontmatter; keeping 'when_to_use' and moving "
                    "'whenToUse' into the body metadata",
                    file_path,
                )
                leftover["whenToUse"] = when_to_use_value

        for key in list(fm.keys()):
            if key not in NATIVE_FIELDS:
                leftover[key] = fm.pop(key)

        moved_count += len(leftover)

        if leftover:
            metadata_yaml = yaml.safe_dump(
                leftover, sort_keys=False, allow_unicode=True)
            body = f"{body}\n## Metadata\n\n```yaml\n{metadata_yaml}```\n"

        new_content = frontmatter_module.join(fm, body)
        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")

        return AdapterMessage(
            message="Adapted {count} frontmatter field(s)",
            params={"count": moved_count},
        )
