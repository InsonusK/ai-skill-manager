# Discovery architecture / Архитектура обнаружения

This document describes how `ai-skill-manager` discovers skills from local directories, files, and GitHub repositories.
Этот документ описывает, как `ai-skill-manager` обнаруживает навыки в локальных директориях, файлах и репозиториях GitHub.

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
├── github.py                 # GitHubDiscovery implementation / Реализация GitHubDiscovery
└── __init__.py               # Public exports / Публичные экспорты
```

Only two concrete discovery strategies remain:
Осталось только две конкретные стратегии обнаружения:

- `AutoDiscovery` — detects any supported skill format.
  `AutoDiscovery` — обнаруживает любой поддерживаемый формат навыка.
- `GitHubDiscovery` — downloads a GitHub archive and delegates to `AutoDiscovery`.
  `GitHubDiscovery` — скачивает архив GitHub и делегирует работу `AutoDiscovery`.

`DiscoveryStrategy` is the abstract base class.
`DiscoveryStrategy` — абстрактный базовый класс.

Skill patterns live in `base/` and are reused by `AutoDiscovery`.
Паттерны навыков находятся в `base/` и переиспользуются `AutoDiscovery`.

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

## `GitHubDiscovery` behavior / Поведение `GitHubDiscovery`

`GitHubDiscovery` downloads the repository archive for the specified `tree`, extracts it to a temporary directory, and processes each configured `subpath` with `AutoDiscovery`.
`GitHubDiscovery` скачивает архив репозитория для указанного `tree`, распаковывает его во временную директорию и обрабатывает каждый настроенный `subpath` с помощью `AutoDiscovery`.

- If a subpath is a directory, `AutoDiscovery` scans it recursively.
  Если подпуть — директория, `AutoDiscovery` рекурсивно её сканирует.
- If a subpath is a `*.skill.md` file, it is treated as a HumanFlat skill.
  Если подпуть — файл `*.skill.md`, он считается навыком HumanFlat.
- Missing subpaths are silently skipped.
  Отсутствующие подпути пропускаются без ошибки.

## Adding a new format / Добавление нового формата

To add a new skill format:
Чтобы добавить новый формат навыка:

1. Create a new pattern class in `base/` that inherits from `SkillPattern`.
   Создать в `base/` новый класс паттерна, наследующий `SkillPattern`.
2. Register it in either `_FLAT_PATTERNS` or `_DIR_PATTERNS` on `AutoDiscovery` in `auto.py`.
   Зарегистрировать его в `_FLAT_PATTERNS` или `_DIR_PATTERNS` класса `AutoDiscovery` в `auto.py`.
3. Update this documentation and `docs/config.md`.
   Обновить этот документ и `docs/config.md`.

No changes are required in `GitHubDiscovery` because it delegates to `AutoDiscovery`.
В `GitHubDiscovery` изменения не требуются, так как он делегирует работу `AutoDiscovery`.
