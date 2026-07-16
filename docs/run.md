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
    - document the sync command
    - list options and examples for the command
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

Use `--dry-run` to validate a source without writing anything: it fully
materializes every skill into a scratch directory (catching structural and
link errors the same way a real sync would) and reports the result, but
never touches the target directory or leaves anything behind.

Используйте `--dry-run`, чтобы проверить источник, ничего не записывая: он
полностью материализует каждый навык во временной директории (обнаруживая
структурные ошибки и ошибки ссылок так же, как это сделала бы настоящая
синхронизация) и выводит результат, но никогда не трогает целевую
директорию и не оставляет после себя файлов.

---

## Global options / Глобальные опции

| Option / Опция | Description / Описание |
|----------------|------------------------|
| `--profile` | Enable execution profiling and print top calls by cumulative, total, and call count. / Включить профилирование выполнения и вывести топ вызовов по накопительному, общему времени и числу вызовов. |
| `--profile-output <file>` | Save raw profiling data to a ``.prof`` file (default: `ai-skill-manager.prof`). / Сохранить сырые данные профилирования в файл ``.prof`` (по умолчанию: `ai-skill-manager.prof`). |

Profiling can also be enabled without the flag by setting the environment variable
``AI_SKILL_MANAGER_PROFILE=1``.

Профилирование можно включить и без флага, установив переменную окружения
``AI_SKILL_MANAGER_PROFILE=1``.

```bash
# Profile a sync run
# Профилировать запуск синхронизации
ai-skill-manager --profile sync

# Profile a dry-run and save raw stats for external tools
# Профилировать dry-run и сохранить сырые данные для внешних инструментов
ai-skill-manager --profile --profile-output sync.prof sync --dry-run

# Enable profiling via environment variable
# Включить профилирование через переменную окружения
AI_SKILL_MANAGER_PROFILE=1 ai-skill-manager sync

# Show help for any command
# Показать справку по любой команде
ai-skill-manager --help
ai-skill-manager <command> --help
```

---

## Opening profile dumps / Открытие файлов профилирования

When ``--profile`` is used, the CLI also writes a raw ``.prof`` file (default:
``ai-skill-manager.prof``). You can inspect it with the standard library or
third-party visualizers.

При использовании ``--profile`` CLI также записывает сырые данные в файл
``.prof`` (по умолчанию: ``ai-skill-manager.prof``). Его можно изучить
стандартными средствами Python или сторонними визуализаторами.

### Standard library / Стандартная библиотека

```bash
python -m pstats ai-skill-manager.prof
```

Inside the interactive shell you can run commands such as:

```
strip_dirs
sort_stats cumulative
stats 30
quit
```

### snakeviz (interactive flamegraph)

Install and launch a browser-based viewer:

```bash
pip install snakeviz
snakeviz ai-skill-manager.prof
```

### gprof2dot (static call graph)

Convert the profile to a PNG/SVG graph:

```bash
pip install gprof2dot
python -m gprof2dot -f pstats ai-skill-manager.prof | dot -Tpng -o profile.png
```
