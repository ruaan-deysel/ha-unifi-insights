# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## GitHub is used for everything

GitHub is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. Run `scripts/setup` to install dependencies.
3. If you've changed something, update the documentation.
4. Make sure your code passes all checks (`pre-commit run --all-files`).
5. Test your contribution (`pytest`).
6. Issue that pull request!

## Any contributions you make will be under the Apache 2.0 License

In short, when you submit code changes, your submissions are understood to be under the same [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

This project uses:

- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- [mypy](https://mypy.readthedocs.io/) for type checking (strict mode)
- [Bandit](https://bandit.readthedocs.io/) for security scanning

Run `pre-commit run --all-files` to lint, format, and type-check your code before submitting, or `scripts/lint` to auto-format and fix linting issues.

## AI Agent Support

This project is **AI agents ready**. Whether you use GitHub Copilot, Claude Code, Gemini, or other AI coding assistants, the repository includes structured instructions to help you work efficiently.

### Agent instruction files

- **[`AGENTS.md`](AGENTS.md)** — Master instruction file (single source of truth for all AI agents)
- **[`CLAUDE.md`](CLAUDE.md)** — Quick reference for Claude Code
- **[`GEMINI.md`](GEMINI.md)** — Quick reference for Gemini
- **[`.github/copilot-instructions.md`](.github/copilot-instructions.md)** — Auto-loaded by GitHub Copilot

### Path-specific instructions

The `.github/instructions/` directory contains context-aware instruction files that GitHub Copilot automatically loads based on the file you're editing. Other AI agents can reference these files manually for domain-specific guidance on Python patterns, entity platforms, coordinators, config flows, and more.

### Reusable prompt templates

The `.github/prompts/` directory contains reusable templates for common tasks:

- **Add New Sensor** — Create sensors with proper structure
- **Add Action** — Implement service actions with validation
- **Add Config Option** — Add configuration options to flows
- **Add Entity to Device** — Expand device capabilities
- **Debug Coordinator Issue** — Diagnose data update problems
- **Update Translations** — Manage multilingual strings
- **Review Integration** — Comprehensive quality review

**Example usage in Copilot Chat:**

```text
#file:Add New Sensor.prompt.md Add a CPU temperature sensor for UniFi devices
```

## Code Quality

This integration follows Home Assistant's [integration quality standards](https://developers.home-assistant.io/docs/core/integration-quality-scale/) as best practices:

- Comprehensive type hints (mypy strict mode)
- Full async patterns for all I/O
- Config flow with reauth and reconfigure support
- Multi-coordinator architecture for efficient data fetching
- 90% minimum test coverage

## Test your code modification

This project comes with a complete development environment in a container, easy to launch if you use Visual Studio Code. With this container you will have a standalone Home Assistant instance running and already configured.

You can also run tests using `pytest` to ensure your changes don't break existing functionality.

## License

By contributing, you agree that your contributions will be licensed under its Apache 2.0 License.
