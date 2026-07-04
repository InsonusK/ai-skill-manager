---
name: ai-skill-manager-changelog
description: Changelog for ai-skill-manager releases in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - changelog
    - release
    - bilingual
  responsibilities:
    - document notable changes for each release
    - highlight new features, fixes, and breaking changes
---

# Changelog / История изменений

All notable changes to this project will be documented in this file.
Все значимые изменения этого проекта будут документироваться в этом файле.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
и проект следует [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-04

### Added / Добавлено

- Production-ready Python CLI packaging with `pyproject.toml` metadata.
  Производственная упаковка Python CLI с метаданными `pyproject.toml`.
- GitHub installation instructions in `README.md` and `docs/install.md`.
  Инструкции по установке из GitHub в `README.md` и `docs/install.md`.
- Linux, macOS, and Windows setup examples.
  Примеры базовой настройки для Linux, macOS и Windows.
- Link to the public skills repository <https://github.com/InsonusK/ai-skills.git>.
  Ссылка на публичный репозиторий навыков <https://github.com/InsonusK/ai-skills.git>.
- MIT `LICENSE` file.
  Файл лицензии MIT.

### Changed / Изменено

- `docs/run.md` now documents the `check` command instead of the removed `discover` command.
  В `docs/run.md` теперь документируется команда `check` вместо удалённой команды `discover`.

### Fixed / Исправлено

- Makefile target `profile-discover` replaced with `profile-check`.
  Цель Makefile `profile-discover` заменена на `profile-check`.
