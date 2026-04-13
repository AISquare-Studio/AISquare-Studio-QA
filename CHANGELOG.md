# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Skip `test-self-autoqa` CI job on Dependabot PRs that lack access to repository secrets (`OPENAI_API_KEY`), preventing false CI failures on dependency update PRs

## [0.2.0] - 2026-03-16

### Added

- `.github/copilot-instructions.md` — repository custom instructions file for GitHub Copilot, providing architecture reference, file layout, CI/CD, configuration, linting, testing, security model, and a mandatory session checklist so that AI agents can work without redundant codebase exploration
- Enhancement roadmap (`docs/AUTOQA_ENHANCEMENT_ROADMAP.md`) with 16 feature proposals inspired by Lucent AI and Meticulous AI, organized into 4 implementation phases targeting reduced human intervention and tighter QA coverage
- Proposal 16: AI-Generated PR Test Criteria — AutoQA analyzes code diffs and generates test criteria for developer review, eliminating the need for developers to manually write test steps in PR descriptions
- `TestCriteriaGenerator` module (`src/autoqa/criteria_generator.py`) implementing Proposal 16: auto-generates test criteria from PR diffs using LLM, posts suggestions as PR comments, supports approval via reaction/comment/label, tier inference from file paths, and auto-proceed for high-confidence criteria
- `auto-criteria` execution mode in `action.yml` and `action_runner.py` for automated criteria generation workflow
- Auto-criteria configuration section in `config/autoqa_config.yaml` with mode, threshold, approval mechanism, and tier inference settings
- New action inputs: `auto-criteria-fallback`, `auto-criteria-mode`, `auto-criteria-threshold`, `auto-criteria-approval`
- New action outputs: `auto_criteria_results`, `criteria`
- Comprehensive test suite for `TestCriteriaGenerator` with 51 unit tests (`tests/test_criteria_generator.py`)

### Changed

- Migrated agent instructions from root `INSTRUCTIONS.md` to `.github/copilot-instructions.md` per GitHub repository custom instructions best practices — GitHub Copilot now reads these instructions automatically
- Updated `README.md` contributing section to reference `.github/copilot-instructions.md`

### Removed

- `INSTRUCTIONS.md` — replaced by `.github/copilot-instructions.md`

### Fixed

- Updated deprecated `actions/checkout@v4` to `@v6` in `action.yml`, examples, and docs — resolves CI failures caused by Node.js 20 deprecation on GitHub Actions runners
- Updated `actions/upload-artifact@v4` to `@v7` in examples and docs for consistency with `action.yml`
- Aligned all action version references in `docs/ARCHITECTURE.md` (`actions/cache@v3`→`@v5`, `actions/setup-python@v4`→`@v6`)
- Fixed upstream repo checkout failure caused by `github.action_ref` resolving to `v6` (from `actions/checkout@v6` step ref) inside the composite action instead of the composite action's own invocation ref — removed unreliable `github.action_ref` from the checkout ref fallback chain and changed `action-ref` input default to `main`

## [0.1.0] - 2026-03-08

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
- Updated `action.yml` checkout ref to derive from `action-ref` input (defaults to `main`); removed `github.action_ref` which resolved incorrectly inside composite actions
- Bumped `actions/cache` from 3 to 5 ([#10](https://github.com/AISquare-Studio/AISquare-Studio-QA/pull/10))
- Bumped `actions/setup-python` from 4 to 6 ([#11](https://github.com/AISquare-Studio/AISquare-Studio-QA/pull/11))
- Bumped `actions/upload-artifact` from 4 to 7 ([#12](https://github.com/AISquare-Studio/AISquare-Studio-QA/pull/12))
- Bumped `stefanzweifel/git-auto-commit-action` from 5 to 7 ([#13](https://github.com/AISquare-Studio/AISquare-Studio-QA/pull/13))

### Fixed

- Fixed release workflow test to use correct parser API (`extract_autoqa_block`)
- Fixed release workflow flake8 flag from `--ignore` to `--extend-ignore` for consistency
