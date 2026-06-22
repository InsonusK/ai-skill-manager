---
name: ai-skill-manager-run
description: CLI command reference for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - cli
    - commands
    - bilingual
  responsibilities:
    - document sync, discover, and new commands
    - list options and examples for each command
---

# Running / Запуск

The CLI is organized into subcommands. Each command has its own options and output format.
CLI разделён на подкоманды. У каждой команды свои опции и формат вывода.

```bash
ai-skill-manager <command> [options]
aism <command> [options]
```

---

## `sync`

Synchronize skills from the config file to the target directory.
Синхронизирует навыки из файла конфигурации в целевую директорию.

### Usage / Использование

```bash
ai-skill-manager sync [options]
```

### Options / Опции

| Option / Опция | Description / Описание |
|----------------|------------------------|
| `-c, --config <path>` | Config file path (default: `ai-skills.yaml`). / Путь к файлу конфигурации (по умолчанию: `ai-skills.yaml`). |
| `--target <dir>` | Override the target directory. / Переопределить целевую директорию. |
| `--on-conflict <error\|last_wins>` | Conflict resolution strategy. / Стратегия разрешения конфликтов имён. |
| `--remove-orphans` | Remove skills not present in the config. / Удалить навыки, отсутствующие в конфиге. |
| `--keep-orphans` | Keep orphan skills. / Оставить осиротевшие навыки. |
| `--dry-run` | Preview changes without writing anything. / Показать изменения без записи. |
| `-f, --force` | Force copy all skills, skip hash/version checks. / Принудительно скопировать все навыки, пропустив проверку хеша и версии. |
| `-v, --verbose` | Enable debug logging. / Включить подробное логирование. |

### Examples / Примеры

```bash
# Sync using default config
# Синхронизация с конфигом по умолчанию
ai-skill-manager sync

# Preview changes
# Предварительный просмотр изменений
ai-skill-manager sync --dry-run

# Use custom config
# Использовать свой конфиг
ai-skill-manager sync -c ./config/my-skills.yaml

# Override target directory
# Переопределить целевую директорию
ai-skill-manager sync --target ./my-skills

# Force full re-copy
# Принудительно перекопировать все навыки
ai-skill-manager sync -f
```

---

## `discover`

Discover skills and print their mappings without copying anything.
Обнаруживает навыки и выводит их сопоставления без копирования.

### Usage / Использование

```bash
ai-skill-manager discover [options]
```

### Options / Опции

| Option / Опция | Description / Описание |
|----------------|------------------------|
| `-c, --config <path>` | Discover from config file. / Обнаружить из файла конфигурации. |
| `-t, --type <auto\|directory\|flat\|github>` | Discovery strategy for a single source. / Стратегия обнаружения для одного источника. |
| `-p, --path <path>` | Source path or GitHub URL. / Путь к источнику или URL GitHub. |
| `--target <dir>` | Override target directory. / Переопределить целевую директорию. |
| `--tree <branch>` | Git tree/branch when `type=github` (default: `master`). / Ветка Git при `type=github` (по умолчанию: `master`). |
| `--subpath <path>` | GitHub subpath (can be repeated). / Подпуть в GitHub (можно повторять). |
| `-v, --verbose` | Enable debug logging. / Включить подробное логирование. |

### Examples / Примеры

```bash
# Discover from default config
# Обнаружить из конфига по умолчанию
ai-skill-manager discover

# Discover from a single local source
# Обнаружить из одного локального источника
ai-skill-manager discover -t auto -p ./my-skills

# Discover from GitHub
# Обнаружить из GitHub
ai-skill-manager discover -t github -p https://github.com/owner/skills-repo.git

# Discover a specific subpath in a GitHub repo
# Обнаружить конкретный подпуть в репозитории GitHub
ai-skill-manager discover -t github \
  -p https://github.com/owner/skills-repo.git \
  --tree main \
  --subpath skills \
  --subpath docs/guides.skill.md
```

---

## `new`

Create a new skill from a template.
Создаёт новый навык из шаблона.

### Usage / Использование

```bash
ai-skill-manager new <skill_name> <path> [options]
```

### Arguments / Аргументы

| Argument / Аргумент | Description / Описание |
|---------------------|------------------------|
| `skill_name` | Name of the new skill. / Имя нового навыка. |
| `path` | Target path. / Целевой путь. |

### Options / Опции

| Option / Опция | Description / Описание |
|----------------|------------------------|
| `--type <flat\|dir>` | Skill type: `flat` creates a single `.md` file, `dir` creates a folder with `SKILL.md` (default: `dir`). / Тип навыка: `flat` создаёт один `.md` файл, `dir` создаёт папку с `SKILL.md` (по умолчанию: `dir`). |

### Examples / Примеры

```bash
# Create a directory skill
# Создать навык в виде директории
ai-skill-manager new my-skill ./my-skill

# Create a flat skill
# Создать плоский навык
ai-skill-manager new my-skill ./my-skill.md --type flat
```

---

## Global options / Глобальные опции

```bash
ai-skill-manager --help
ai-skill-manager <command> --help
```
