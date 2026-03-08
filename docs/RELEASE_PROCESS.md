# Release Process

This document describes how to create releases for AISquare Studio AutoQA.

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (`v2.0.0`) — Breaking changes to action inputs, outputs, or behavior
- **MINOR** (`v1.1.0`) — New features, new inputs/outputs (backward compatible)
- **PATCH** (`v1.0.1`) — Bug fixes, documentation updates (backward compatible)

### Version Tags

Each release creates two types of tags:

| Tag | Example | Purpose |
|-----|---------|---------|
| Full version | `v1.2.3` | Immutable, pinned release |
| Major version | `v1` | Floating tag, always points to latest `v1.x.x` |

Users reference the action by major version for automatic minor/patch updates:

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@v1
```

Or pin to an exact version for maximum stability:

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@v1.2.3
```

## Release Pipeline

The release pipeline is fully automated via `.github/workflows/release.yml`. Pushing a version tag triggers the following:

```
Tag push (v1.2.3)
  ├── Validate action.yml structure
  ├── Lint (black, isort, flake8)
  ├── Test (parser validation)
  └── Release (after all checks pass)
        ├── Extract release notes from CHANGELOG.md
        ├── Create GitHub Release
        └── Update major version tag (v1 → v1.2.3)
```

### Pre-release Versions

Tags containing a hyphen (e.g., `v1.0.0-beta.1`) are automatically marked as pre-releases on GitHub. These are useful for testing before a stable release.

## How to Create a Release

### 1. Update the Changelog

Edit `CHANGELOG.md` to move items from `[Unreleased]` to the new version:

```markdown
## [Unreleased]

## [1.2.3] - 2025-06-15

### Added
- New feature description

### Fixed
- Bug fix description
```

### 2. Commit the Changelog

```bash
git add CHANGELOG.md
git commit -m "Prepare release v1.2.3"
git push origin main
```

### 3. Create and Push the Tag

```bash
git tag v1.2.3
git push origin v1.2.3
```

This triggers the release workflow which will:
- Validate the action
- Run linting and tests
- Create the GitHub Release with notes from the changelog
- Update the `v1` major version tag

### 4. Verify the Release

1. Check the [Actions tab](https://github.com/AISquare-Studio/AISquare-Studio-QA/actions/workflows/release.yml) for the workflow run
2. Check the [Releases page](https://github.com/AISquare-Studio/AISquare-Studio-QA/releases) for the new release
3. Verify the major version tag points to the new release:
   ```bash
   git ls-remote --tags origin | grep -E 'v[0-9]+$'
   ```

## GitHub Marketplace

### Initial Marketplace Listing

To list this action on the GitHub Marketplace for the first time:

1. Go to the repository's [Releases page](https://github.com/AISquare-Studio/AISquare-Studio-QA/releases)
2. Click **Draft a new release** (or edit an existing release)
3. Check **Publish this Action to the GitHub Marketplace**
4. GitHub will validate that `action.yml` has the required fields:
   - `name` — unique across the marketplace
   - `description`
   - `branding.icon` and `branding.color`
5. Select the primary and secondary categories
6. Publish the release

### Subsequent Releases

After the initial marketplace listing, every new GitHub Release automatically updates the marketplace listing. No additional steps are required.

### Marketplace Requirements

The following are already configured in `action.yml`:

| Requirement | Status | Value |
|-------------|--------|-------|
| `name` | ✅ | AISquare Studio AutoQA |
| `description` | ✅ | AI-powered test generation... |
| `branding.icon` | ✅ | zap |
| `branding.color` | ✅ | blue |
| `author` | ✅ | AISquare Studio |

## Hotfix Process

For critical fixes that need immediate release:

1. Create a fix on `main`
2. Update `CHANGELOG.md` with the fix
3. Tag with the next patch version (e.g., `v1.2.4`)
4. Push the tag to trigger the release pipeline

## Rolling Back a Release

If a release has issues:

1. **Revert the major version tag** to the previous stable release:
   ```bash
   git tag -fa v1 v1.2.2 -m "Rollback v1 to v1.2.2"
   git push origin v1 --force
   ```

2. **Mark the bad release as pre-release** on GitHub to warn users

3. **Fix the issue** and release a new patch version
