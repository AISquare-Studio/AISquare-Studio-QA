# Contributing to AISquare Studio AutoQA

Thank you for your interest in contributing to AISquare Studio AutoQA! This guide will help you get started.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/AISquare-Studio/AISquare-Studio-QA/issues/new?template=bug_report.md) using the bug report template. Include as much detail as possible:

- Steps to reproduce
- Expected vs. actual behavior
- Workflow configuration (redact secrets)
- Relevant logs or screenshots

### Suggesting Features

Have an idea? [Open a feature request](https://github.com/AISquare-Studio/AISquare-Studio-QA/issues/new?template=feature_request.md) describing the problem you're solving and your proposed solution.

### Submitting Pull Requests

1. **Fork** the repository and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add or update tests** for your changes
4. **Run linting and tests** to verify nothing is broken
5. **Submit a pull request** using the PR template

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Local Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/AISquare-Studio-QA.git
cd AISquare-Studio-QA

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install flake8==7.0.0 black==24.4.2 isort==5.13.2

# Install Playwright browsers
playwright install chromium
```

### Environment Configuration

Copy the environment template and fill in your values:

```bash
cp env.template .env
```

## Coding Standards

### Style

- **Formatter:** [Black](https://black.readthedocs.io/) with default settings
- **Import sorting:** [isort](https://pycqa.github.io/isort/) with Black-compatible profile
- **Linting:** [Flake8](https://flake8.pycqa.org/) with configuration in `.flake8`

### Running Linters

```bash
# Format code
black .
isort .

# Check for lint errors
flake8 .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test markers
pytest -m smoke
pytest -m "not slow"
```

## Pull Request Guidelines

When submitting a pull request, please ensure:

- **Clear intent:** State which problem you're solving and why
- **Quality:** No spelling mistakes, readable code
- **Tests:** Include or update tests for your changes
- **Documentation:** Update docs if your change affects usage
- **Scope:** Keep PRs focused — one feature or fix per PR
- **Commits:** Write clear, descriptive commit messages

## Project Structure

```
├── action.yml              # GitHub Action definition
├── src/
│   ├── agents/             # CrewAI agents (planner, executor)
│   ├── autoqa/             # Action logic (runner, parser, reporter)
│   ├── crews/              # CrewAI orchestration
│   ├── execution/          # Iterative execution engine
│   ├── templates/          # Test execution templates
│   ├── tools/              # Playwright & DOM tools
│   └── utils/              # Utility modules
├── tests/                  # Test suite
├── config/                 # Configuration files
├── docs/                   # Documentation
└── examples/               # Example configurations
```

## Security

If you discover a security vulnerability, **do not** open a public issue. Please see our [Security Policy](SECURITY.md) for responsible disclosure instructions.

## License

By contributing to this project, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
