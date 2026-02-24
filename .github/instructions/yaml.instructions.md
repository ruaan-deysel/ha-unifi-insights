---
applyTo: "**/*.yaml, **/*.yml"
---

# YAML Instructions

**Applies to:** All YAML files

## Formatting

- 2-space indentation
- No tabs
- Use modern HA syntax (no legacy `platform:` style)
- Quote strings that could be misinterpreted (e.g., `"on"`, `"off"`, `"yes"`, `"no"`)

## Key Files

- `services.yaml` — Service action schema definitions
- `.github/workflows/*.yml` — CI/CD workflows
- `.pre-commit-config.yaml` — Pre-commit hook configuration
- `config/configuration.yaml` — Local dev HA config

## services.yaml

Legacy filename (now called "service actions"). Defines schemas only — names and descriptions go in `strings.json` translations.

```yaml
service_name:
  fields:
    parameter:
      required: true
      selector:
        text:
```

## GitHub Workflows

- Use pinned action versions (`@v4`, not `@main`)
- Minimize secrets exposure
- Use `permissions` to restrict token scope
