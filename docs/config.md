---
name: ai-skill-manager-config
description: Configuration file reference for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - config
    - yaml
    - bilingual
  responsibilities:
    - document ai-skills.yaml structure
    - describe sources, settings, and conflict resolution
    - provide config examples
---

# Configuration / Конфигурация

The configuration file controls where skills are discovered and how they are synchronized.
Файл конфигурации управляет тем, где обнаруживаются навыки и как они синхронизируются.

## File format / Формат файла

The config file can be **YAML** (`.yaml` / `.yml`) or **JSON** (`.json`).
Файл конфигурации может быть в формате **YAML** (`.yaml` / `.yml`) или **JSON** (`.json`).

Default file name: `ai-skills.yaml`
Имя файла по умолчанию: `ai-skills.yaml`

## Top-level structure / Структура верхнего уровня

```yaml
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
  dry_run: false
```

## `sources` / Источники

List of source locations to scan for skills. Each source is a dictionary with the following fields:
Список источников для сканирования навыков. Каждый источник — словарь со следующими полями:

| Field / Поле | Required / Обязательное | Default / По умолчанию | Description / Описание |
|--------------|-------------------------|------------------------|------------------------|
| `path` | Yes / Да | — | Directory path relative to the config file (or GitHub repo URL when `type: github`). / Путь к директории относительно файла конфигурации (или URL репозитория GitHub при `type: github`). |
| `type` | No / Нет | `auto` | Source type: `auto` (local filesystem) or `github`. Values `flat` and `directory` are accepted for backward compatibility and treated as `auto`. / Тип источника: `auto` (локальная файловая система) или `github`. Значения `flat` и `directory` принимаются для обратной совместимости и обрабатываются как `auto`. |
| `name` | No / Нет | — | Explicit skill name override. / Явное переопределение имени навыка. |

### Discovery types / Типы обнаружения

#### `auto`

Recursively scans the source path and automatically detects the skill format.
Рекурсивно сканирует источник и автоматически определяет формат навыка.

Supported formats / Поддерживаемые форматы:

- **Agent** — a directory containing `SKILL.md`.
  **Agent** — директория, содержащая `SKILL.md`.
- **HumanDir** — a directory named `{name}` containing `{name}.skill.md`.
  **HumanDir** — директория с именем `{name}`, содержащая `{name}.skill.md`.
- **HumanFlat** — a single file named `*.skill.md`.
  **HumanFlat** — один файл с именем `*.skill.md`.

`auto` resolves ambiguities and reports errors for conflicting patterns:
`auto` разрешает неоднозначности и сообщает об ошибках при конфликтующих паттернах:

- If a file matches more than one flat pattern, an error is raised.
  Если файл соответствует более чем одному плоскому паттерну, выдаётся ошибка.
- If a directory matches more than one directory pattern, an error is raised.
  Если директория соответствует более чем одному директориальному паттерну, выдаётся ошибка.
- If a directory matches both a directory pattern and unrelated flat files, an error is raised.
  Если директория соответствует директориальному паттерну и при этом содержит сторонние плоские файлы, выдаётся ошибка.
- A chosen directory skill cannot contain nested skills.
  Выбранный директориальный навык не может содержать вложенные навыки.

Example source / Пример источника:

```
my-skills/
  guide.skill.md          # HumanFlat
  web/
    web.skill.md          # HumanDir
  agent/
    SKILL.md              # Agent
    extra.md              # regular file, ignored as a skill
```

#### `flat` and `directory`

These types are kept for backward compatibility and are internally mapped to `auto`.
Эти типы сохранены для обратной совместимости и внутренне замаплены на `auto`.

They no longer have separate behavior; `auto` detects all supported formats.
Они больше не имеют отдельного поведения; `auto` обнаруживает все поддерживаемые форматы.

#### `github`

Downloads a GitHub repository archive and discovers skills from one or more subpaths within it.
Скачивает архив репозитория GitHub и обнаруживает навыки в одном или нескольких подпутях внутри него.

**Additional fields / Дополнительные поля:**

| Field / Поле | Required / Обязательное | Default / По умолчанию | Description / Описание |
|--------------|-------------------------|------------------------|------------------------|
| `path` | Yes / Да | — | GitHub repository URL (`https` or `ssh` format). / URL репозитория GitHub (формат `https` или `ssh`). |
| `tree` | No / Нет | `master` | Branch or tag name to checkout. / Имя ветки или тега для скачивания. |
| `subpath` | No / Нет | `skills` | Path or list of paths inside the repo to scan for skills. / Путь или список путей внутри репозитория для сканирования навыков. |

Each subpath is processed using **auto** logic:
Каждый подпуть обрабатывается логикой **auto**:

- If the path is a directory, it is scanned recursively using `auto` rules.
  Если путь — директория, она рекурсивно сканируется по правилам `auto`.
- If the path is a single `*.skill.md` file, it is treated as a HumanFlat skill.
  Если путь — один файл `*.skill.md`, он считается навыком HumanFlat.
- Missing paths are silently skipped.
  Отсутствующие пути пропускаются без ошибки.

Example with a single subpath / Пример с одним подпутём:

```yaml
sources:
  - path: https://github.com/owner/skills-repo.git
    type: github
    tree: main
    subpath: skills
```

Example with multiple subpaths / Пример с несколькими подпутями:

```yaml
sources:
  - path: https://github.com/owner/skills-repo.git
    type: github
    tree: main
    subpath:
      - skills
      - docs/guides.skill.md
```

### Combining local and GitHub sources / Комбинирование локальных и GitHub-источников

```yaml
sources:
  - path: ./my-skills
    type: auto
  - path: https://github.com/owner/shared-skills.git
    type: github
    tree: main
    subpath:
      - skills
      - playbooks

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

## `settings` / Настройки

Global settings that apply to the synchronization.
Глобальные настройки, применяемые при синхронизации.

| Setting / Настройка | Type / Тип | Default / По умолчанию | Description / Описание |
|---------------------|------------|------------------------|------------------------|
| `target` | string / строка | `.agents/skills` | Target directory relative to the config file. / Целевая директория относительно файла конфигурации. |
| `remove_orphans` | boolean / булево | `true` | Remove skills in the target that are no longer defined in the config. / Удалить навыки в целевой директории, которые больше не определены в конфиге. |
| `on_conflict` | string / строка | `error` | How to handle duplicate skill names: `error` or `last_wins`. / Как обрабатывать дублирующиеся имена навыков: `error` или `last_wins`. |
| `dry_run` | boolean / булево | `false` | When `true`, preview changes without writing anything. / При значении `true` показывать изменения без записи. |

### Conflict resolution / Разрешение конфликтов

- `error` — raise an error if two sources produce the same skill name.
  `error` — выдать ошибку, если два источника дают одинаковое имя навыка.
- `last_wins` — the last source in the list wins.
  `last_wins` — побеждает последний источник в списке.

CLI flags (`--target`, `--on-conflict`, `--remove-orphans`, `--keep-orphans`, `--dry-run`) override the config file values.
Флаги CLI (`--target`, `--on-conflict`, `--remove-orphans`, `--keep-orphans`, `--dry-run`) переопределяют значения из файла конфигурации.

### Example with dry-run enabled / Пример с включённым сухим прогоном

```yaml
settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: last_wins
  dry_run: true
```

Run `ai-skill-manager sync` to preview changes without modifying the target directory.
Запустите `ai-skill-manager sync`, чтобы увидеть изменения без изменения целевой директории.
