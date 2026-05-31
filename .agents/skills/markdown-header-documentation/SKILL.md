---
name: Markdown Documentation Metadata
description: Require structured YAML metadata header for all markdown documentation files
---
# VS Code Agent Markdown Metadata Skill (Schema-Compliant)

## Purpose

When generating or updating any documentation `.md` file in a VS Code Agent environment, ensure metadata is **strictly compatible with the supported schema**.

This skill prevents warnings caused by unsupported YAML attributes and enforces correct separation between runtime fields and extended AI metadata.

---

## Hard Constraint: Allowed Top-Level Fields

In agent-compatible YAML frontmatter, ONLY these fields are allowed:

* `name`
* `description`
* `metadata`
* `context`
* `license`
* `compatibility`
* `argument-hint`
* `disable-model-invocation`
* `user-invocable`

Any other top-level field WILL produce warnings and must not be used.

---

## Required Structure

Every markdown file MUST start with:

```yaml
---
name: <stable-identifier>
description: <short semantic summary>
metadata: {}
---
```

---

## Field Semantics

### `name` (required)

* Stable machine identifier
* lowercase, kebab-case recommended
* must not change frequently

Example:

```yaml
name: docker-host-role
```

---

### `description` (required)

* Short semantic explanation
* 1–3 lines max
* used by AI for routing and embedding

Example:

```yaml
description: Manages Docker host provisioning and reverse proxy integration for container exposure.
```

---

### `metadata` (recommended extension layer)

Use `metadata` for ALL additional structured information.

This is the ONLY safe place for extended schema.

Allowed content inside metadata:

* domain
* tags
* responsibilities
* constraints
* dependencies
* ai_hints

Example:

```yaml
metadata:
  domain: infrastructure
  tags:
    - docker
    - nginx
    - ansible
  responsibilities:
    - provision docker host
    - configure reverse proxy routing
  constraints:
    - no direct container port exposure
    - all ingress must go through proxy
  ai_hints:
    priority: high
    idempotent: true
```

---

## Optional Fields (Use Only If Needed)

### `context`

Additional runtime or execution context.

### `license`

License declaration for the document or module.

### `compatibility`

Defines supported environments or agent versions.

### `user-invocable`

Marks whether this document/tool can be directly invoked by user agents.

---

## Prohibited Patterns

Do NOT use these at top level:

```yaml
title: ❌
summary: ❌
type: ❌
tags: ❌ (must be inside metadata)
domain: ❌ (must be inside metadata)
```

These will trigger VS Code agent warnings.

---

## Recommended Pattern (Full Example)

```yaml
---
name: docker-host-role

description: Manages Docker host provisioning and reverse proxy integration for containerized services.

metadata:
  domain: infrastructure
  tags:
    - docker
    - nginx
    - ansible
  responsibilities:
    - provision docker runtime
    - configure reverse proxy routing
  constraints:
    - no direct external port exposure
    - all traffic routed through proxy layer
  ai_hints:
    architecture: declarative
    safety_level: high
---
```

---

## Design Principles

* Keep `name` + `description` minimal and stable
* Push all extensibility into `metadata`
* Treat YAML as a **strict contract**, not free-form notes
* Optimize `description` for AI embedding quality
* Avoid duplication of file contents in metadata

---

## Outcome

Following this structure ensures:

* no VS Code agent warnings
* consistent AI retrieval behavior
* clean separation of contract vs semantic context
* better indexing in RAG systems
