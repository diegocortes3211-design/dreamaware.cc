# Copilot Coding Agent Onboarding Instructions

Welcome to the dreamaware.cc repository! This file provides best practices and onboarding instructions for using GitHub Copilot Coding Agent in this repository.

## Purpose
This repository is configured to support Copilot Coding Agent for automated code changes, PR creation, and collaborative development.

## Best Practices
- **Describe tasks clearly:** When requesting changes, provide clear, actionable instructions and relevant context.
- **Use plans for complex work:** For multi-step or ambiguous tasks, break work into logical phases using TODO lists.
- **Review PRs:** Always review Copilot-generated pull requests for correctness and completeness before merging.
- **Provide feedback:** If Copilot's changes need improvement, leave comments or request updates in the PR.

## Repository Context
- **Main branch:** `main`
- **Project type:** Multi-language, includes Python, TypeScript, shell scripts, and configuration files.
- **Key folders:**
  - `api/`, `services/`, `engine/`, `tests/`, `scripts/`, `site/`
- **Testing:** Python tests in `tests/`, TypeScript in `api/`
- **CI/CD:** See `ci/pipelines/`

## Usage Guidelines
- Use Copilot Coding Agent for:
  - Refactoring code
  - Implementing new features
  - Fixing bugs
  - Updating documentation
  - Managing configuration files
- Avoid using Copilot for:
  - Sensitive credential management
  - Large-scale destructive changes without review

## Additional Resources
- [Copilot Coding Agent Tips](https://gh.io/copilot-coding-agent-tips)
- [Repository README](../README.md)

---
For questions or issues, contact the repository owner or maintainers.
