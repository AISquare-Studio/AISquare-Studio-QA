<!--
Title: [IMPROVE] Pin dependency versions in requirements.txt
Labels: good first issue, dependencies, help wanted
-->

# Pin Dependency Versions in `requirements.txt`

## Summary

All runtime dependencies in `requirements.txt` are currently unpinned, which means builds can
break at any time when upstream packages release breaking changes. This is especially risky for
a GitHub Action where users expect reproducible behavior.

## Current State

```
crewai[tools]
playwright
pytest
pytest-html
pytest-json-report
pytest-xdist
python-dotenv
rich
pyyaml
jinja2
requests
```

None of these have version constraints. A breaking change in any dependency (e.g., CrewAI
redesigning its API, Playwright changing its sync API) would silently break all users.

## What to Do

1. **Determine current working versions** by installing dependencies and checking:
   ```bash
   pip install -r requirements.txt
   pip freeze | grep -i "crewai\|playwright\|pytest\|python-dotenv\|rich\|pyyaml\|jinja2\|requests"
   ```

2. **Pin major versions** using compatible release constraints (`~=` or `>=X.Y,<X+1`):
   ```
   crewai[tools]>=0.80,<1.0
   playwright>=1.40,<2.0
   pytest>=7.0,<9.0
   pytest-html>=4.0,<5.0
   pytest-json-report>=1.5,<2.0
   pytest-xdist>=3.0,<4.0
   python-dotenv>=1.0,<2.0
   rich>=13.0,<14.0
   pyyaml>=6.0,<7.0
   jinja2>=3.1,<4.0
   requests>=2.31,<3.0
   ```

3. **Verify the pinned versions work** by running:
   ```bash
   pip install -r requirements.txt
   pytest --co  # collect tests without running
   python -c "from src.autoqa.parser import AutoQAParser; print('Parser OK')"
   ```

4. **Optionally**, add a `requirements-dev.txt` for development dependencies:
   ```
   -r requirements.txt
   flake8==7.0.0
   black==24.4.2
   isort==5.13.2
   ```

## Why Pin with Ranges (Not Exact Versions)?

- Exact pins (`==`) prevent security patches from being applied automatically
- Range pins (`>=X.Y,<X+1`) allow patch updates while preventing breaking major changes
- Dependabot (already configured in `.github/dependabot.yml`) will submit PRs for version bumps

## Acceptance Criteria

- [ ] All dependencies in `requirements.txt` have version constraints
- [ ] `pip install -r requirements.txt` succeeds with pinned versions
- [ ] Existing tests and linting still pass
- [ ] Dev dependencies are separated from runtime dependencies
