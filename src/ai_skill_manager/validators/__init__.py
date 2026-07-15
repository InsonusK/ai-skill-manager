"""Link exclusion rules package.

Structural validation (``Validator``/``ValidationReport``) was removed:
name-format and duplicate-name checks now live on ``Skill`` and
``SkillDictBuilder`` in the new pipeline. Only the link-exclude rules under
``validators.rules.link`` remain, reused by ``LinkDiscovery``.

Пакет правил исключения ссылок.

Структурная валидация (``Validator``/``ValidationReport``) удалена: проверки
формата имени и дубликатов имён теперь находятся в ``Skill`` и
``SkillDictBuilder`` новой архитектуры. Остались только правила исключения
ссылок в ``validators.rules.link``, переиспользуемые ``LinkDiscovery``.
"""
