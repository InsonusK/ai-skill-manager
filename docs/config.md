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
    - setup
  responsibilities:
    - document ai-skills.yaml structure
    - describe sources, settings, and conflict resolution
    - provide config examples for local and GitHub sources
    - link to the public skills repository
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

## Basic setup examples / Примеры базовой настройки

### Local skills / Локальные навыки

```yaml
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

### Skills from GitHub / Навыки из GitHub

```yaml
sources:
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
    subpath: skills

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

Run `ai-skill-manager sync` to download the configured skills.
Запустите `ai-skill-manager sync`, чтобы скачать настроенные навыки.

A public collection of example skills is maintained at
<https://github.com/InsonusK/ai-skills.git>.
Публичная коллекция примеров навыков поддерживается по адресу
<https://github.com/InsonusK/ai-skills.git>.

## `sources` / Источники

List of source locations to scan for skills. Each source is a dictionary with the following fields:
Список источников для сканирования навыков. Каждый источник — словарь со следующими полями:

| Field / Поле | Required / Обязательное | Default / По умолчанию | Description / Описание |
|--------------|-------------------------|------------------------|------------------------|
| `path` | Yes / Да | — | Directory path relative to the config file (or GitHub repo URL when `type: github`). / Путь к директории относительно файла конфигурации (или URL репозитория GitHub при `type: github`). |
| `type` | No / Нет | `auto` | Source type: `auto` (local filesystem) or `github`. Values `flat` and `directory` are accepted for backward compatibility and treated as `auto`. / Тип источника: `auto` (локальная файловая система) или `github`. Значения `flat` и `directory` принимаются для обратной совместимости и обрабатываются как `auto`. |
| `name` | No / Нет | — | Explicit skill name override. / Явное переопределение имени навыка. |
| `tags` | No / Нет | — | List of tag filter expressions. Skills must match every expression to be included. / Список выражений-фильтров тегов. Навык включается, только если соответствует каждому выражению. |
| `skip_folder` | No / Нет | `["examples"]` | Directory names inside a directory skill that are ignored when checking for nested skills. The directories are still copied as part of the skill. / Имена директорий внутри директориального навыка, которые игнорируются при проверке на вложенные навыки. Сами директории всё равно копируются вместе с навыком. |

#### `tags` syntax / Синтаксис `tags`

Each item in `tags` is a string expression that can use the following operators:
Каждый элемент `tags` — строковое выражение, в котором можно использовать следующие операторы:

| Operator / Оператор | Meaning / Значение |
|---------------------|--------------------|
| `&` | AND — skill must have both tags. / И — навык должен иметь оба тега. |
| `\|` | OR — skill must have at least one of the tags. / ИЛИ — навык должен иметь хотя бы один из тегов. |
| `!` | NOT — skill must not have the tag. / НЕ — навык не должен иметь тега. |
| `(`/`)` | Grouping. / Группировка. |
| `/` | Hierarchical tag separator. / Разделитель иерархических тегов. |

Examples / Примеры:

```yaml
sources:
  - path: ./my-skills
    type: auto
    tags:
      - python & cli
      - "!deprecated"
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
    subpath: skills
    tags:
      - (python & cli) | web
      - a/b/c
```

- `python & cli` — skills tagged with both `python` and `cli`.
  `python & cli` — навыки с тегами `python` и `cli` одновременно.
- `python | cli` — skills tagged with `python` or `cli`.
  `python | cli` — навыки с тегом `python` или `cli`.
- `(python & cli) | web` — skills with both `python` and `cli`, or skills with `web`.
  `(python & cli) | web` — навыки с `python` и `cli`, либо с `web`.
- `!deprecated` — skills without the `deprecated` tag.
  `!deprecated` — навыки без тега `deprecated`.
- `a/b/c` — matches any consecutive segment (`a`, `b`, `c`, `a/b`, `b/c`, `a/b/c`).
  `a/b/c` — совпадает с любым последовательным сегментом (`a`, `b`, `c`, `a/b`, `b/c`, `a/b/c`).

Expressions starting with `!` should be quoted in YAML so they are not parsed as YAML tags:
Выражения, начинающиеся с `!`, следует заключать в кавычки в YAML, чтобы они не воспринимались как YAML-теги:

```yaml
tags:
  - "!deprecated"
```


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
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
    subpath: skills
```

Example with multiple subpaths / Пример с несколькими подпутями:

```yaml
sources:
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
    subpath:
      - skills
      - docs/guides.skill.md
```

### Combining local and GitHub sources / Комбинирование локальных и GitHub-источников

```yaml
sources:
  - path: ./my-skills
    type: auto
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
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
| `target` | string or mapping / строка или отображение | `.agents/skills` | Target directory, or a mapping of multiple named targets. See [Multi-target sync](#multi-target-sync--мульти-target-синхронизация) below. / Целевая директория, либо отображение с несколькими именованными target'ами. См. [Мульти-target синхронизация](#multi-target-sync--мульти-target-синхронизация) ниже. |
| `remove_orphans` | boolean / булево | `true` | Remove skills in the target that are no longer defined in the config. / Удалить навыки в целевой директории, которые больше не определены в конфиге. |
| `on_conflict` | string / строка | `error` | How to handle duplicate skill names: `error` or `last_wins`. / Как обрабатывать дублирующиеся имена навыков: `error` или `last_wins`. |
| `dry_run` | boolean / булево | `false` | When `true`, preview changes without writing anything. / При значении `true` показывать изменения без записи. |

### Validation settings / Настройки валидации

`settings.validation.rules.link.skip_folder` controls which directories are excluded from link validation and link rewriting.
`settings.validation.rules.link.skip_folder` управляет тем, какие директории исключаются из валидации ссылок и их перезаписи.

| Setting / Настройка | Type / Тип | Default / По умолчанию | Description / Описание |
|---------------------|------------|------------------------|------------------------|
| `skip_folder` | list of strings / список строк | `["examples"]` | Folder names whose files are skipped during link validation and adaptation. Use an empty list or `null` to disable folder-based exclusions. / Имена директорий, файлы которых пропускаются при валидации и адаптации ссылок. Используйте пустой список или `null`, чтобы отключить исключения по директориям. |

Example / Пример:

```yaml
settings:
  validation:
    rules:
      link:
        skip_folder:
          - examples
          - another_folder
```

To disable the default `examples` exclusion, use an empty list:
Чтобы отключить встроенное исключение `examples`, используйте пустой список:

```yaml
settings:
  validation:
    rules:
      link:
        skip_folder: []
```

## Multi-target sync / Мульти-target синхронизация

`settings.target` can be a mapping of several named targets instead of a single string. Each target copies **the same discovered skills**, independently, into its own directory with its own adapter list.
`settings.target` может быть отображением из нескольких именованных target'ов вместо одной строки. Каждый target независимо копирует **одни и те же обнаруженные скиллы** в свою директорию со своим списком адаптеров.

```yaml
settings:
  target:
    for_each:
      adapters:
        - link-adapter
    default:
      path: .agents/skills
    claude:
      path: .claude/skills
      adapters:
        - claude-property-adapter
```

- `for_each` — a reserved key, not a target name. Its `adapters` list is merged (added, deduplicated, order-preserving) into every real target's own `adapters` list.
  `for_each` — служебный ключ, не является именем target'а. Его список `adapters` объединяется (с дедупликацией, с сохранением порядка) со списком `adapters` каждого реального target'а.
- Any other top-level key under `target` is a target name with two optional fields: `path` and `adapters` (a list of adapter names, see the table below).
  Любой другой ключ верхнего уровня внутри `target` — это имя target'а с двумя опциональными полями: `path` и `adapters` (список имён адаптеров, см. таблицу ниже).
- `default` and `claude` are **reserved names** with built-in default paths (`.agents/skills` and `.claude/skills` respectively), so `path` can be omitted for them. Any other target name requires an explicit `path` — omitting it is a configuration error, raised when the config is loaded.
  `default` и `claude` — **зарезервированные имена** со встроенными путями по умолчанию (`.agents/skills` и `.claude/skills` соответственно), поэтому для них `path` можно не указывать. Для любого другого имени `path` обязателен — его отсутствие является ошибкой конфигурации, которая выдаётся при загрузке конфига.
- If a target's final adapter list (its own `adapters` plus `for_each.adapters`) ends up empty, it falls back to `link-adapter`, matching the flat-string default.
  Если итоговый список адаптеров target'а (его собственные `adapters` плюс `for_each.adapters`) оказывается пустым, используется `link-adapter`, как и при строковом формате.
- The flat string format (`target: .agents/skills`) still works unchanged — it is equivalent to `target: {default: {path: .agents/skills, adapters: [link-adapter]}}`.
  Строковый формат (`target: .agents/skills`) по-прежнему работает без изменений — он эквивалентен `target: {default: {path: .agents/skills, adapters: [link-adapter]}}`.

### Available adapters / Доступные адаптеры

| Config name / Имя в конфиге | Description / Описание |
|------------------------------|-------------------------|
| `link-adapter` | Rewrites internal links between skills into repo-absolute `skill-link` targets. Used by default. / Переписывает внутренние ссылки между скиллами в repo-absolute `skill-link` цели. Используется по умолчанию. |
| `claude-property-adapter` | Reshapes frontmatter into the fields Claude Code natively understands (`name`, `description`, `when_to_use`, `allowed-tools`, `model`, etc.). Any other frontmatter field is moved into a visible `## Metadata` block in the file body instead of being silently dropped. / Приводит frontmatter к полям, нативно понимаемым Claude Code (`name`, `description`, `when_to_use`, `allowed-tools`, `model` и т.д.). Любое другое поле frontmatter переносится в видимый блок `## Metadata` в теле файла вместо того, чтобы быть молча отброшенным. |

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
