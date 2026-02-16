# Path-Specific Copilot Instructions

This directory contains path-specific instructions that Copilot will apply when working on files in specific areas of the repository.

## How It Works

Each `.instructions.md` file has YAML frontmatter that specifies which files it applies to:

```yaml
---
applyTo: "path/pattern/**"
description: "What this instruction covers"
---
```

## Instructions Files

### scripts.instructions.md
- **Applies to:** `scripts/**/*.py`
- **Purpose:** Python coding standards, error handling, authentication patterns
- **Use when:** Working on deployment scripts and utilities

### workspaces.instructions.md
- **Applies to:** `workspaces/**`
- **Purpose:** Fabric item conventions, naming patterns, configuration files
- **Use when:** Adding or modifying Fabric workspace items

### workflows.instructions.md
- **Applies to:** `.github/workflows/**/*.yml`, `.github/workflows/**/*.yaml`
- **Purpose:** GitHub Actions patterns, secrets handling, deployment triggers
- **Use when:** Modifying CI/CD workflows

## Copilot Behavior

When you ask Copilot to work on a file:

1. Copilot reads the main `.github/copilot-instructions.md`
2. Copilot checks if any path-specific instructions match the file
3. Copilot combines both sets of instructions
4. Copilot applies the guidance to its work

## Benefits

- **Context-aware**: Different guidelines for different code areas
- **Specialized**: Targeted patterns for scripts vs. workspaces vs. workflows
- **Consistent**: Ensures uniform coding standards across the repository

## Adding New Instructions

To add instructions for a new path:

1. Create a new `.instructions.md` file in this directory
2. Add YAML frontmatter with `applyTo` pattern
3. Write guidance specific to that code area
4. Reference examples and patterns from existing code

Example:
```markdown
---
applyTo: "docs/**/*.md"
description: "Documentation writing guidelines"
---

# Documentation Instructions

## Writing Style
- Use clear, concise language
- Include code examples
- ...
```

## References

- [GitHub Copilot Instructions Guide](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Main Copilot Instructions](../copilot-instructions.md)
