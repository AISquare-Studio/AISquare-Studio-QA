# Code Quality and Linting

This project uses automated linting to maintain code quality and consistency.

## Linting Tools

- **Black**: Code formatter for consistent style
- **isort**: Import statement organizer
- **flake8**: Linter for code quality and PEP 8 compliance

## Configuration

### Line Length
- Maximum line length: **100 characters**

### Ignored Rules
- `E203`: Whitespace before ':' (conflicts with Black)
- `W503`: Line break before binary operator (outdated PEP 8)
- `E501`: Line too long (handled by Black)

### Excluded Files/Directories
- `__pycache__/`, `venv/`, `.venv/`, `.env/`
- `build/`, `dist/`, `*.egg-info/`
- `reports/`, `test-results/`, `playwright-report/`
- `src/templates/test_execution_template.py` (contains placeholders)
- `tests/generated/` (auto-generated test files)

## Automated Linting

### GitHub Actions Workflow
The linting workflow runs automatically on:
- **Push to `main` branch**: Checks code but doesn't commit
- **Pull requests**: Automatically fixes and commits linting issues
- **Manual trigger**: Via workflow dispatch

### Workflow File
`.github/workflows/lint.yml`

## Local Development

### Install Linting Tools
```bash
pip install flake8==7.0.0 black==24.4.2 isort==5.13.2
```

Or uncomment the dev dependencies in `requirements.txt` and run:
```bash
pip install -r requirements.txt
```

### Run Linting Locally

#### Format code with Black
```bash
black . --line-length=100 --preview --enable-unstable-feature=string_processing
```

#### Organize imports with isort
```bash
isort . --profile=black --line-length=100
```

#### Check code with flake8
```bash
flake8 .
```

#### Run all linting tools at once
```bash
black . --line-length=100 --preview --enable-unstable-feature=string_processing && \
isort . --profile=black --line-length=100 && \
flake8 .
```

## Configuration Files

- **`.flake8`**: Flake8 configuration
- **`pyproject.toml`**: Black and isort configuration
- **`.github/workflows/lint.yml`**: GitHub Actions workflow

## Pre-commit Hook (Optional)

To automatically run linting before each commit, install pre-commit:

```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        args: [--line-length=100, --preview]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
```

Then install the hooks:
```bash
pre-commit install
```

## VS Code Integration

Add to `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--line-length=100",
    "--preview"
  ],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=100"
  ],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## PyCharm/IntelliJ Integration

1. **Black**: Settings → Tools → Black → Enable on save
2. **isort**: Settings → Tools → isort → Enable on save
3. **flake8**: Settings → Editor → Inspections → Python → Enable flake8

## Troubleshooting

### Linting workflow fails
- Check the workflow logs in GitHub Actions
- Run linting locally to identify issues
- Ensure all excluded files are properly configured

### Import order issues
- Run `isort . --profile=black --line-length=100`
- Check that isort is using the black profile

### Line length violations
- Black should handle most line length issues automatically
- For complex cases, you may need to manually break lines
- Use parentheses for implicit line continuation

### Template file errors
- Template files (with `{{PLACEHOLDERS}}`) are excluded from linting
- Add any new template files to the exclude list in `.flake8`

## Best Practices

1. **Run linting locally** before pushing
2. **Fix issues incrementally** rather than all at once
3. **Use meaningful variable names** to improve readability
4. **Keep functions focused** (max complexity: 15)
5. **Add docstrings** to public functions and classes
6. **Use type hints** for better code clarity
