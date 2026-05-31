---
name: workflow-work-summary

description: Guidelines for writing a structured summary after completing a task. Uses a template to generate timestamped markdown files in .agent-logs.

metadata:
  domain: workflow
  tags:
  - workflow
  - summary
  - reporting
  - agent-logs
  ai_hints:
    category: workflow
---

# When to use skill
When you have finished task

# How to use it
1. Useing [summary template](templates/summary.md.j2) create summary file in directory `.agent-logs` file name must be `{timestamp}_{task name up to 10 words}.md`
