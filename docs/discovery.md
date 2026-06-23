---
name: ai-skill-manager-discovery
description: Discovery architecture and behavior for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - discovery
    - architecture
    - bilingual
  responsibilities:
    - explain AutoDiscovery and Source-based scanning
    - document supported skill formats
    - describe how to add a new skill format
---

# Discovery architecture / Архитектура обнаружения

This document describes how `ai-skill-manager` discovers skills from local directories, files, and GitHub repositories.
Этот документ описывает, как `ai-skill-manager` обнаруживает навыки в локальных директориях, файлах и репозиториях GitHub.

## Source abstraction / Абстракция источника

Every place skills come from is represented by a :class:`Source` entity in
``src/ai_skill_manager/entities/source/``. A source knows how to turn itself
into a local :class:`ScanLocation` (``repo_path`` + ``source_path``) via
``get_scan_location()``.

Каждое место, откуда приходят навыки, представлено сущностью :class:`Source`
в ``src/ai_skill_manager/entities/source/``. Источник умеет превращать себя
в локальную :class:`ScanLocation` (``repo_path`` + ``source_path``) через
``get_scan_location()``.

- ``repo_path`` — absolute path to the repository root. Used for resolving
  ``repo_absolute`` links.
  ``repo_path`` — абсолютный путь к корню репозитория. Используется для
  разрешения ссылок ``repo_absolute``.
- ``source_path`` — absolute path to the directory that ``AutoDiscovery``
  should scan. Becomes ``Skill.source_path``.
  ``source_path`` — абсолютный путь к директории, которую ``AutoDiscovery``
  должен сканировать. Становится ``Skill.source_path``.

### Supported source types / Поддерживаемые типы источников

- :class:`LocalSource` — a local file or directory.
  :class:`LocalSource` — локальный файл или директория.
- :class:`GitHubSource` — a GitHub repository. ``get_scan_location()``
  downloads and extracts the repository archive to a temporary directory.
  :class:`GitHubSource` — репозиторий GitHub. ``get_scan_location()``
  скачивает и распаковывает архив репозитория во временную директорию.

## Source layout / Структура модуля

The discovery code lives in `src/ai_skill_manager/discovery/source/`.
Код обнаружения находится в `src/ai_skill_manager/discovery/source/`.

```
src/ai_skill_manager/discovery/source/
├── DiscoveryStrategy.py      # Abstract base class / Абстрактный базовый класс
├── base/
│   ├── __init__.py           # Exports all skill patterns / Экспортирует все паттерны навыков
│   ├── SkillPattern.py       # Abstract pattern / Абстрактный паттерн
│   ├── HumanFlatPattern.py   # HumanFlat matcher / Сопоставитель HumanFlat
│   ├── HumanDirPattern.py    # HumanDir matcher / Сопоставитель HumanDir
│   └── AgentPattern.py       # Agent matcher / Сопоставитель Agent
├── auto.py                   # AutoDiscovery implementation / Реализация AutoDiscovery
└── __init__.py               # Public exports / Публичные экспорты
```

Only one concrete discovery strategy remains:
Осталась только одна конкретная стратегия обнаружения:

- `AutoDiscovery` — detects any supported skill format from a local scan path.
  `AutoDiscovery` — обнаруживает любой поддерживаемый формат навыка из локального пути сканирования.

`DiscoveryStrategy` is the abstract base class.
`DiscoveryStrategy` — абстрактный базовый класс.

Skill patterns live in `base/` and are reused by `AutoDiscovery`.
Паттерны навыков находятся в `base/` и переиспользуются `AutoDiscovery`.

Source acquisition (for example downloading a GitHub archive) is the
responsibility of the :class:`Source` implementation, not of the discovery
strategy.

Захват источника (например, скачивание архива GitHub) является ответственностью
реализации :class:`Source`, а не стратегии обнаружения.

## Supported skill formats / Поддерживаемые форматы навыков

| Format / Формат | Location / Расположение | Marker / Маркер |
|-----------------|-------------------------|-----------------|
| Agent | Directory / Директория | `SKILL.md` |
| HumanDir | Directory / Директория | `{dir_name}.skill.md` |
| HumanFlat | File / Файл | `*.skill.md` |

## `AutoDiscovery` behavior / Поведение `AutoDiscovery`

`AutoDiscovery` accepts either a file or a directory as the source path.
`AutoDiscovery` принимает в качестве источника либо файл, либо директорию.

### File input / Входной файл

When the source path is a file, it is checked against all flat patterns.
Когда источник — файл, он проверяется по всем плоским паттернам.

- 0 matches → returns `[]`.
  0 совпадений → возвращает `[]`.
- 1 match → returns `[Skill]`.
  1 совпадение → возвращает `[Skill]`.
- >1 matches → raises `ValueError: Skill definition conflict inFile ...`.
  >1 совпадений → выдаёт `ValueError: Skill definition conflict inFile ...`.

### Directory input / Входная директория

When the source path is a directory, two checks are performed:
Когда источник — директория, выполняются две проверки:

1. Flat-pattern check on every file directly inside the directory.
   Проверка плоских паттернов для каждого файла непосредственно в директории.
2. Directory-pattern check on the directory itself.
   Проверка директориальных паттернов для самой директории.

Based on the matches, the following decisions are made:
На основе совпадений принимаются следующие решения:

| Directory matches / Директориальные совпадения | Flat matches / Плоские совпадения | Result / Результат |
|------------------------------------------------|-----------------------------------|--------------------|
| 0 | 0 | Recurse into subdirectories. / Рекурсия в поддиректории. |
| 0 | >0 | Add flat skills and recurse. / Добавить плоские навыки и рекурсия. |
| 1 | 0 | Validate no nested skills, then add the directory skill. / Проверить отсутствие вложенных навыков, затем добавить директориальный навык. |
| 1 | 1, same file / 1, тот же файл | Treat as directory skill, validate no nested skills, then add. / Считать директориальным навыком, проверить отсутствие вложенных, затем добавить. |
| 1 | 1, different files / 1, разные файлы | Raise `Cannot unambiguously determine skill`. / Выдать `Cannot unambiguously determine skill`. |
| 1 | >1 | Raise `Skill definition conflict`. / Выдать `Skill definition conflict`. |
| >1 | any / любое | Raise `Skill definition conflict`. / Выдать `Skill definition conflict`. |

### Nested skill validation / Проверка вложенных навыков

A directory that is chosen as a skill must not contain nested skills.
Директория, выбранная в качестве навыка, не должна содержать вложенных навыков.

The validation recursively scans the directory tree and raises:
Проверка рекурсивно сканирует дерево директорий и выдаёт ошибку:

- `Nested skills detected in directory skill: ...` if another skill pattern is found inside.
  `Nested skills detected in directory skill: ...`, если внутри найден другой паттерн навыка.

## GitHub source behavior / Поведение источника GitHub

:class:`GitHubSource` downloads the repository archive for the specified
`tree`, extracts it to a temporary directory, and returns a :class:`ScanLocation`
where ``repo_path`` is the repository root and ``source_path`` is the configured
``subpath``.

:class:`GitHubSource` скачивает архив репозитория для указанного `tree`,
распаковывает его во временную директорию и возвращает :class:`ScanLocation`,
где ``repo_path`` — корень репозитория, а ``source_path`` — настроенный
``subpath``.

- If a subpath is a directory, `AutoDiscovery` scans it recursively.
  Если подпуть — директория, `AutoDiscovery` рекурсивно её сканирует.
- If a subpath is a `*.skill.md` file, it is treated as a HumanFlat skill.
  Если подпуть — файл `*.skill.md`, он считается навыком HumanFlat.
- Missing subpaths are silently skipped.
  Отсутствующие подпути пропускаются без ошибки.
- ``repo_absolute`` links are resolved against ``repo_path``, not ``source_path``.
  Ссылки ``repo_absolute`` разрешаются относительно ``repo_path``, а не ``source_path``.

### GitHub discovery example / Пример обнаружения из GitHub

```bash
ai-skill-manager discover -t github \
  -p https://github.com/owner/skills-repo.git \
  --tree main \
  --subpath skills \
  --subpath docs/quickstart.skill.md
```

## Adding a new format / Добавление нового формата

To add a new skill format:
Чтобы добавить новый формат навыка:

1. Create a new pattern class in `base/` that inherits from `SkillPattern`.
   Создать в `base/` новый класс паттерна, наследующий `SkillPattern`.
2. Register it in either `_FLAT_PATTERNS` or `_DIR_PATTERNS` on `AutoDiscovery` in `auto.py`.
   Зарегистрировать его в `_FLAT_PATTERNS` или `_DIR_PATTERNS` класса `AutoDiscovery` в `auto.py`.
3. Update this documentation and `docs/config.md`.
   Обновить этот документ и `docs/config.md`.

No changes are required in source implementations as long as they produce a
valid :class:`ScanLocation`, because discovery delegates to `AutoDiscovery`.

Изменения в реализациях источников не требуются, пока они производят корректную
:class:`ScanLocation`, так как обнаружение делегирует работу `AutoDiscovery`.
