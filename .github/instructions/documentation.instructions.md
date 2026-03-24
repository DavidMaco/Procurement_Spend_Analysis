---
applyTo: "**"
description: "Documentation, README, and commit message standards for Procurement Spend Analysis."
---

# Documentation Standard

## Writing Style

- Write in natural language with direct, specific sentences.
- Do not use em dashes. Rewrite the sentence, use a comma, or use a colon.
- Do not open documents with generic preambles.
- No AI boilerplate. Every paragraph must say something concrete about this repository.
- Prefer active voice.

## README Standard

README files follow a structured narrative pattern derived from the PVIS repository standard:

1. One-line descriptor, a precise factual summary.
2. Business problem, the concrete pain the project addresses.
3. Capabilities, only implemented features.
4. Architecture diagram, preferably Mermaid.
5. Data model, useful enough for a new developer.
6. Key methodology, with formulas when the project uses quantitative models.
7. Business impact, in operational terms.
8. Quick start or deliverables, only the minimum required steps or outputs.

README files must not include:

- claims about capabilities that are not implemented
- generic feature tables that could apply to any repository
- filler text that does not help a contributor operate or understand the system

## Documentation Files

- Keep one topic per file.
- Use specific titles.
- Update docs when the described behavior changes.
- Do not create placeholder docs that only announce that docs exist.

## Commit Message Standard

Use conventional commits:

```text
type(scope): summary message
```

Rules:

- One logical change per commit.
- Summary uses imperative mood and stays within 72 characters.
- Valid types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `security`, `perf`.
- Scope names the affected layer or module.
- Security fixes use `security(scope):` and should note the risk category in the body.

Do not use vague commit messages such as `fix stuff`, `updates`, `WIP`, or `changes`.
