# Release Process

This document describes how to create releases for AISquare Studio AutoQA.

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (`v2.0.0`) — Breaking changes to action inputs, outputs, or behavior
- **MINOR** (`v1.1.0`) — New features, new inputs/outputs (backward compatible)
- **PATCH** (`v1.0.1`) — Bug fixes, documentation updates (backward compatible)

### Version Tags

Each release creates **one** tag, and it never moves:

| Tag | Example | Purpose |
|-----|---------|---------|
| Full version | `v0.3.0` | Immutable. The only thing consumers should reference. |

**There is deliberately no floating major tag.** Maintaining a `vN` tag that always points at the
newest `vN.x.x` requires `git tag -fa` plus `git push --force` on every release, which silently
retargets every consumer the instant a release lands — including a bad one. AutoQA sat broken from
2026-01-15 to 2026-08-03 precisely because a mutable reference kept serving stale content while
looking current, so this repo does not use that pattern.

Consumers pin an exact version:

```yaml
- uses: AISquare-Studio/AISquare-Studio-QA@v0.3.0
```

Upgrading is a deliberate one-line PR in the consuming repo. That is the point: you find out you
are upgrading, and a bad release cannot reach anyone who did not opt in.

> **Legacy:** a `v0` tag still exists on origin from before this change and currently points at the
> same commit as `v0.3.0`. It is **frozen** — no workflow updates it any more, so it will drift and
> become misleading. Do not reference it. It should be deleted once nothing points at it; the
> release workflow emits a warning on every run while it exists.

## Release Pipeline

The release pipeline is fully automated via `.github/workflows/release.yml`. Pushing a version tag triggers the following:

```
Tag push (v1.2.3)
  ├── Validate action.yml structure
  ├── Lint (black, isort, flake8)
  ├── Test (parser validation)
  └── Release (after all checks pass)
        ├── Extract release notes from CHANGELOG.md
        └── Create GitHub Release   (immutable tag; no mutable tag is moved)
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

It does **not** move any existing tag.

### 4. Verify the Release

1. Check the [Actions tab](https://github.com/AISquare-Studio/AISquare-Studio-QA/actions/workflows/release.yml) for the workflow run
2. Check the [Releases page](https://github.com/AISquare-Studio/AISquare-Studio-QA/releases) for the new release
3. Confirm no mutable tag was moved — this should list only the frozen legacy `v0`:
   ```bash
   git ls-remote --tags origin | grep -E 'refs/tags/v[0-9]+$'
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

Tags here are immutable, so there is nothing to move backwards — and that is deliberate. A
rollback is a **roll forward**:

1. **Mark the bad release as pre-release** on GitHub so it stops being "Latest" and is visibly
   flagged.

2. **Fix the issue and release the next patch version** (e.g. `v0.3.1`). Consumers pinned to the
   bad exact version are unaffected until they bump, which is the whole benefit of exact pins —
   a bad release cannot reach anyone who did not opt in.

3. **Tell the consumers who already bumped** to pin back to the last good version, e.g.
   `@v0.2.0`. Because the reference is exact, pinning back is a one-line revert in their repo
   and needs no cooperation from this one.

Do **not** reintroduce a force-pushed floating tag to make rollback feel faster. A mutable
reference is what let AutoQA serve a broken build for six months while reporting success.
