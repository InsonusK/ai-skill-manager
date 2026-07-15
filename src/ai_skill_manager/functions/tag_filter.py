"""Tag expression parser and skill filter.

Парсер выражений тегов и фильтр навыков.

Supported syntax / Поддерживаемый синтаксис:
- ``tag`` — exact tag match (or hierarchical subpath match).
- ``tag1 & tag2`` — both tags must be present.
- ``tag1 | tag2`` — at least one tag must be present.
- ``!tag`` — tag must be absent.
- ``(tag1 & tag2) | tag3`` — grouping.
- ``tag1/tag2/tag3`` — hierarchical tag; matches any consecutive segment
  such as ``tag1``, ``tag2``, ``tag3``, ``tag1/tag2``, ``tag2/tag3`` or
  ``tag1/tag2/tag3``.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Sequence, Set


#: Callable that tests a normalized set of skill tags.
#: Вызываемый объект, проверяющий нормализованное множество тегов навыка.
TagMatcher = Callable[[Set[str]], bool]


def _normalize_tag_set(tags: Iterable[str]) -> Set[str]:
    """Return a set of stripped non-empty tag strings.

    Возвращает множество непустых тегов без крайних пробелов.
    """
    return {tag.strip() for tag in tags if tag and str(tag).strip()}


def _tag_variants(tag: str) -> List[str]:
    """Return all consecutive segments of a hierarchical tag.

    Для иерархического тега возвращает все последовательные сегменты.

    ``a/b/c`` produces ``['a', 'b', 'c', 'a/b', 'b/c', 'a/b/c']``.
    A tag without slashes produces a list containing only itself.
    """
    parts = [part for part in tag.split("/") if part]
    if not parts:
        return []
    if len(parts) == 1:
        return [tag]
    variants: List[str] = []
    for start in range(len(parts)):
        for end in range(start + 1, len(parts) + 1):
            variants.append("/".join(parts[start:end]))
    return variants


def _matches_tag(skill_tags: Set[str], tag_term: str) -> bool:
    """Check whether a skill tag set satisfies a single tag term.

    Проверяет, удовлетворяет ли множество тегов навыка одному теговому терму.
    """
    return any(variant in skill_tags for variant in _tag_variants(tag_term))


class _TagNode:
    """Leaf node representing a single tag term."""

    def __init__(self, tag: str):
        self.tag = tag

    def __call__(self, skill_tags: Set[str]) -> bool:
        return _matches_tag(skill_tags, self.tag)


class _AndNode:
    """Binary AND node."""

    def __init__(self, left: TagMatcher, right: TagMatcher):
        self.left = left
        self.right = right

    def __call__(self, skill_tags: Set[str]) -> bool:
        return self.left(skill_tags) and self.right(skill_tags)


class _OrNode:
    """Binary OR node."""

    def __init__(self, left: TagMatcher, right: TagMatcher):
        self.left = left
        self.right = right

    def __call__(self, skill_tags: Set[str]) -> bool:
        return self.left(skill_tags) or self.right(skill_tags)


class _NotNode:
    """Unary NOT node."""

    def __init__(self, operand: TagMatcher):
        self.operand = operand

    def __call__(self, skill_tags: Set[str]) -> bool:
        return not self.operand(skill_tags)


class _Parser:
    """Recursive-descent parser for tag expressions."""

    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> TagMatcher:
        """Parse the token list into a matcher.

        Разбирает список токенов в matcher.
        """
        node = self._parse_or()
        if self.pos != len(self.tokens):
            raise ValueError(
                f"Unexpected token '{self.tokens[self.pos]}' at position {self.pos}"
            )
        return node

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, expected: str | None = None) -> str:
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of tag expression")
        if expected is not None and token != expected:
            raise ValueError(f"Expected '{expected}' but got '{token}'")
        self.pos += 1
        return token

    def _parse_or(self) -> TagMatcher:
        left = self._parse_and()
        while self._peek() == "|":
            self._consume("|")
            right = self._parse_and()
            left = _OrNode(left, right)
        return left

    def _parse_and(self) -> TagMatcher:
        left = self._parse_not()
        while self._peek() == "&":
            self._consume("&")
            right = self._parse_not()
            left = _AndNode(left, right)
        return left

    def _parse_not(self) -> TagMatcher:
        if self._peek() == "!":
            self._consume("!")
            return _NotNode(self._parse_not())
        return self._parse_primary()

    def _parse_primary(self) -> TagMatcher:
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of tag expression")
        if token == "(":
            self._consume("(")
            node = self._parse_or()
            self._consume(")")
            return node
        if token in (")",
                    "&",
                    "|",
                    "!",
                    ):
            raise ValueError(f"Unexpected token '{token}'")
        self._consume()
        return _TagNode(token)


def _tokenize(expression: str) -> List[str]:
    """Split an expression into operator and tag tokens.

    Разделяет выражение на токены операторов и тегов.
    """
    tokens: List[str] = []
    i = 0
    length = len(expression)
    while i < length:
        char = expression[i]
        if char.isspace():
            i += 1
            continue
        if char in "()&|!":
            tokens.append(char)
            i += 1
            continue
        start = i
        while i < length and not expression[i].isspace() and expression[i] not in "()&|!":
            i += 1
        tokens.append(expression[start:i])
    return tokens


def compile_tag_expression(expression: str) -> TagMatcher:
    """Compile a tag expression into a reusable matcher.

    Компилирует выражение тегов в reusable matcher.

    Args:
        expression: Tag expression string. / Строка с выражением тегов.

    Returns:
        Callable that accepts a set of skill tags and returns ``True`` if the
        expression matches. / Вызываемый объект, принимающий множество тегов
        навыка и возвращающий ``True``, если выражение совпадает.

    Raises:
        ValueError: If the expression syntax is invalid.
    """
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty tag expression")
    return _Parser(tokens).parse()


def matches_tag_expressions(skill_tags: Sequence[str], expressions: Sequence[str]) -> bool:
    """Return ``True`` if a skill satisfies all tag expressions.

    Возвращает ``True``, если навык удовлетворяет всем выражениям тегов.

    An empty expression list matches every skill. A skill matches a non-empty
    list only when every expression evaluates to ``True``.
    """
    if not expressions:
        return True
    tag_set = _normalize_tag_set(skill_tags)
    matchers = [compile_tag_expression(expr) for expr in expressions]
    return all(matcher(tag_set) for matcher in matchers)


def _skill_frontmatter_tags(skill: Any) -> Sequence[str]:
    """Return a discovered skill's own frontmatter ``tags``.

    Возвращает собственные frontmatter ``tags`` обнаруженного скилла.
    """
    # Import here to avoid a circular import at module load time.
    # EN: Lazy import because entities may import this module in the future.
    # RU: Ленивый импорт, потому что entities могут импортировать этот модуль.
    from ..entities.skill_kind import SkillKind
    from ..entities.skill_propetry import SkillProperty

    main_file = (
        skill.path if skill.kind is SkillKind.flat else skill.path / skill.main_file_relative_path
    )
    return SkillProperty(main_file).tags


def filter_skills_by_tags(skills: Sequence[Any], expressions: Sequence[str]) -> List[Any]:
    """Return only skills that match all tag expressions.

    Возвращает только навыки, соответствующие всем выражениям тегов.
    """
    if not expressions:
        return list(skills)

    matchers = [compile_tag_expression(expr) for expr in expressions]
    result: List[Any] = []
    for skill in skills:
        tag_set = _normalize_tag_set(_skill_frontmatter_tags(skill))
        if all(matcher(tag_set) for matcher in matchers):
            result.append(skill)
    return result
