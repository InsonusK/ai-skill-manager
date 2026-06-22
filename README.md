---
name: ai-skill-manager-readme
description: Project overview and quick start guide for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - readme
    - quickstart
    - bilingual
  responsibilities:
    - introduce the project
    - provide quick start examples
    - link to detailed documentation
---

# AI Skills Manager / Менеджер навыков ИИ

Sync AI agent skills into `.agents/skills/` from local directories or GitHub repositories.
Синхронизирует навыки AI-агентов в `.agents/skills/` из локальных директорий или репозиториев GitHub.

## Quick start / Быстрый старт

Create an `ai-skills.yaml` config in your project root:
Создайте конфиг `ai-skills.yaml` в корне проекта:

```yaml
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

Run the sync:
Запустите синхронизацию:

```bash
ai-skill-manager sync
# or use the short alias / или используйте короткий псевдоним
aism sync
```

## Documentation / Документация

- [Installation / Установка](docs/install.md)
- [Running / Запуск](docs/run.md)
- [Configuration / Конфигурация](docs/config.md)
- [Discovery architecture / Архитектура обнаружения](docs/discovery.md)

## What it does / Что делает утилита

- Discovers skills from local directories (`auto`, `flat`, `directory`) or GitHub repositories.
  Обнаруживает навыки в локальных директориях (`auto`, `flat`, `directory`) или репозиториях GitHub.
- Copies them to a target directory (default: `.agents/skills`).
  Копирует их в целевую директорию (по умолчанию: `.agents/skills`).
- Removes orphan skills that are no longer in the config (optional).
  Удаляет осиротевшие навыки, которых больше нет в конфиге (опционально).
- Updates internal links so they point to the correct target paths.
  Обновляет внутренние ссылки, чтобы они указывали на правильные целевые пути.
- Supports dry-run mode to preview changes safely.
  Поддерживает режим сухого прогона для безопасного предпросмотра изменений.

## Skill types / Типы навыков

### `flat`

Each `.md` file becomes its own skill directory with a `SKILL.md` inside.
Каждый файл `.md` становится собственной директорией навыка с файлом `SKILL.md` внутри.

```
my-skills/
  guide.md   → .agents/skills/guide/SKILL.md
  tips.md    → .agents/skills/tips/SKILL.md
```

### `directory`

Each subdirectory containing `SKILL.md` is copied as-is.
Каждая поддиректория, содержащая `SKILL.md`, копируется как есть.

```
my-skills/
  web/
    SKILL.md   → .agents/skills/web/SKILL.md
    extra.md   → .agents/skills/web/extra.md
```

### `auto` (default / по умолчанию)

Automatically detects whether a directory should be treated as `directory` (contains `SKILL.md`) or `flat`.
Автоматически определяет, следует ли обрабатывать директорию как `directory` (содержит `SKILL.md`) или `flat`.

`auto` also recognizes the human-friendly formats `*.skill.md` and `{name}/{name}.skill.md`.
`auto` также распознаёт человекочитаемые форматы `*.skill.md` и `{name}/{name}.skill.md`.

## Example workflow / Пример workflow

1. Create a local skills folder / Создайте локальную папку с навыками:

   ```bash
   mkdir -p ./my-skills
   ```

2. Add a skill / Добавьте навык:

   ```bash
   ai-skill-manager new git-workflow ./my-skills/git-workflow
   ```

3. Preview the sync / Предпросмотр синхронизации:

   ```bash
   ai-skill-manager sync --dry-run
   ```

4. Run the sync / Запустите синхронизацию:

   ```bash
   ai-skill-manager sync
   ```

5. Check the installed skills / Проверьте установленные навыки:

   ```bash
   ls .agents/skills
   ```
