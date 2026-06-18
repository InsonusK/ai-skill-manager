"""New skill API.

Public functions create skills and return Path objects instead of printing
output. This makes them reusable from other commands or scripts.

Публичные функции создают навыки и возвращают объекты Path вместо вывода
в консоль. Это позволяет переиспользовать их из других команд или скриптов.
"""

from pathlib import Path
from typing import Literal

SkillType = Literal["flat", "dir"]
#: Allowed skill types. / Допустимые типы навыков.

SKILL_TEMPLATE = """---
name: {name}
description: _skill description_
version: 1.0.0
---

# When use skill
_Usecase when skill applied_

# Goal
_Goal of applying this skill_

# Requirements
_What ai agent should define before apply skill_

# Implementation
_Implementation plan_
"""
#: Template content for a new SKILL.md file. / Шаблон содержимого нового файла SKILL.md.


class SkillExistsError(FileExistsError):
    """Raised when the target skill file or directory already exists.

    Возникает, когда целевой файл или директория навыка уже существуют.
    """


def create_skill(skill_name: str, path: Path, skill_type: SkillType) -> Path:
    """Create a new skill and return the created path.

    Создаёт новый навык и возвращает путь к созданному объекту.

    Args:
        skill_name: Name of the new skill. / Имя нового навыка.
        path: Target path. For flat skills it may be a file or directory.
            For directory skills it must be the directory to create.
            / Целевой путь. Для плоских навыков это может быть файл или директория.
            Для навыков-директорий это должна быть создаваемая директория.
        skill_type: ``flat`` for a single ``<name>.md`` file,
            ``dir`` for a folder containing ``SKILL.md``.
            / ``flat`` — один файл ``<name>.md``,
            ``dir`` — папка с файлом ``SKILL.md``.

    Returns:
        Path to the created file (flat) or directory (dir).
        / Путь к созданному файлу (flat) или директории (dir).

    Raises:
        SkillExistsError: If the target already exists.
            / Если целевой объект уже существует.

    Example:
        >>> from pathlib import Path
        >>> create_skill("hello", Path("./skills/hello"), "dir")
        PosixPath('/.../skills/hello')
    """
    # Resolve the path to avoid relative path ambiguity.
    # Разрешаем путь, чтобы избежать неоднозначности относительных путей.
    path = path.resolve()

    # Ensure the parent directory exists before creating the skill.
    # Убеждаемся, что родительская директория существует перед созданием навыка.
    path.parent.mkdir(parents=True, exist_ok=True)

    if skill_type == "flat":
        # Flat skill: either a concrete file or a file inside a directory.
        # Плоский навык: либо конкретный файл, либо файл внутри директории.
        target_file = path / f"{skill_name}.md" if path.is_dir() else path

        if target_file.exists():
            raise SkillExistsError(f"File already exists: {target_file}")

        target_file.write_text(
            SKILL_TEMPLATE.format(name=skill_name), encoding="utf-8"
        )
        return target_file

    # Directory skill: the path itself is the skill folder.
    # Навык-директория: сам путь является папкой навыка.
    if path.exists():
        raise SkillExistsError(f"Path already exists: {path}")

    path.mkdir(parents=True, exist_ok=False)
    target_file = path / "SKILL.md"
    target_file.write_text(SKILL_TEMPLATE.format(name=skill_name), encoding="utf-8")
    return path
