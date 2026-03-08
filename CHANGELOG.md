# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-05-01

### Added

- Initial release of AISquare Studio AutoQA
- AI-powered test generation from PR descriptions using CrewAI + Playwright
- Active Execution Mode with step-by-step browser interaction
- Smart selector discovery via DOMInspectorTool
- Intelligent retry with alternative selectors
- AST-based security validation for generated code
- Cross-repository test file management
- PR comment reporting with screenshots
- ETag-based idempotency
- Multi-tier test organization (A/B/C tiers)
- Multi-layer caching (pip, Playwright, repository)
- Lint workflow (`lint.yml`)
- Test workflow (`test-action.yml`)
- Bug report and feature request issue templates
- Contributing guidelines and Code of Conduct
- Apache 2.0 license
- Security policy (`SECURITY.md`)
- Changelog (`CHANGELOG.md`)
- Support documentation (`SUPPORT.md`)
- Pull request template (`.github/PULL_REQUEST_TEMPLATE.md`)
- Code owners file (`.github/CODEOWNERS`)
- Dependabot configuration (`.github/dependabot.yml`)
- Funding configuration (`.github/FUNDING.yml`)
- Automated release pipeline (`.github/workflows/release.yml`)
- Release process documentation (`docs/RELEASE_PROCESS.md`)

### Changed

- Expanded `CONTRIBUTING.md` with development setup, testing, and coding standards
- Updated `README.md` license section to reference Apache 2.0 license
- Enhanced issue templates with labels and GitHub Action-specific context
- Fixed `action.yml` checkout ref to use `github.action_ref` for version-pinned releases

### Fixed

- Fixed release workflow test to use correct parser API (`extract_autoqa_block`)
- Fixed release workflow flake8 flag from `--ignore` to `--extend-ignore` for consistency
