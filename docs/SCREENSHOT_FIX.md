# 🖼️ Screenshot Fix for AutoQA PR Comments

## Problem
Screenshots were not appearing in AutoQA PR comments because:

1. **Path Resolution Issue**: Screenshots were saved to `reports/screenshots/` in the action's workspace (`.autoqa-action/`), but the reporter was looking for them in the target repository's workspace.

2. **No Artifact Upload**: The GitHub Action workflow didn't upload screenshots as artifacts, so they were lost after the workflow completed.

3. **Relative Path Conflicts**: The screenshot paths were relative, causing issues when trying to access them from different working directories.

## Solution

### 1. **Fixed Screenshot Path Resolution** 📍

#### Changes in `src/agents/executor_agent.py` and `executor_agent_fixed.py`:
- Screenshots now use the `ACTION_PATH` environment variable to save to the correct location
- Paths are constructed using `os.path.join()` for cross-platform compatibility
- Both success and error screenshots now save to the action's workspace

```python
# Before (❌ Incorrect)
screenshot_path = f"reports/screenshots/test_completion_{timestamp}.png"

# After (✅ Correct)
action_path = os.getenv('ACTION_PATH', '.')
screenshot_path = os.path.join(action_path, f"reports/screenshots/test_completion_{timestamp}.png")
```

### 2. **Enhanced Screenshot Resolution in Reporter** 🔍

#### Changes in `src/autoqa/reporter.py`:
- Added `_resolve_screenshot_path()` method to check multiple locations
- Checks:
  1. Absolute path (if provided)
  2. Relative to current directory
  3. Relative to GitHub workspace
  4. Relative to action path
- Added fallback to GitHub Actions artifacts link if screenshot can't be embedded

```python
def _resolve_screenshot_path(self, screenshot_path: str) -> Optional[Path]:
    """Resolve screenshot path to absolute path, checking multiple locations"""
    # Checks multiple locations and returns the first valid path
```

### 3. **Added Artifact Upload Steps** 📦

#### Changes in `action.yml`:
- Added two new steps after test execution:
  1. **Upload Screenshots**: Uploads all PNG files from screenshot directories
  2. **Upload Test Reports**: Uploads complete reports and test files

```yaml
- name: 📸 Upload Screenshots as Artifacts
  if: always() && steps.autoqa.outputs.test_generated == 'true'
  uses: actions/upload-artifact@v4
  with:
    name: autoqa-screenshots-${{ github.run_number }}
    path: |
      .autoqa-action/reports/screenshots/*.png
      ${{ github.workspace }}/reports/screenshots/*.png
    if-no-files-found: warn
    retention-days: 30

- name: 📊 Upload Test Reports
  if: always() && steps.autoqa.outputs.test_generated == 'true'
  uses: actions/upload-artifact@v4
  with:
    name: autoqa-reports-${{ github.run_number }}
    path: |
      .autoqa-action/reports/**
      ${{ github.workspace }}/reports/**
      ${{ inputs.test-directory }}/**
    if-no-files-found: warn
    retention-days: 30
```

### 4. **PR Comment Enhancement** 💬

#### Changes in `src/autoqa/reporter.py`:
- Added direct link to GitHub Actions artifacts in the PR comment
- Shows a clickable link to view all artifacts and screenshots
- Provides fallback message if screenshot embedding fails

```markdown
### 📁 Generated Artifacts
- 📄 **Test File:** `tests/generated/test_login.py`
- 📦 **[View All Artifacts & Screenshots](https://github.com/owner/repo/actions/runs/12345)**

### 📸 Success Screenshot
![Success Screenshot](data:image/png;base64,...)
```

## How It Works Now

### Workflow Overview:
```
1. Test Execution
   └─> Save screenshot to: .autoqa-action/reports/screenshots/test_completion_20250101_120000.png

2. Reporter Process
   ├─> Resolve screenshot path (check multiple locations)
   ├─> Try to embed screenshot (base64 for small images, GitHub upload for large)
   └─> Add artifacts link to PR comment

3. Artifact Upload (GitHub Actions)
   ├─> Upload screenshots artifact
   └─> Upload reports artifact

4. PR Comment
   ├─> Embedded screenshot (if small enough)
   ├─> Artifacts link (always)
   └─> Fallback message (if embedding failed)
```

## Benefits

### ✅ Multiple Screenshot Access Methods:

1. **Embedded in PR Comment**: Small screenshots (<100KB) are embedded directly using base64
2. **GitHub Artifacts**: All screenshots are uploaded as artifacts for 30 days
3. **Direct Link**: PR comments include a clickable link to view all artifacts

### ✅ Reliability:

- Works regardless of screenshot size
- No dependency on external image hosting
- Artifacts persist even if PR is closed
- Multiple fallback mechanisms

### ✅ Developer Experience:

- Screenshots visible directly in PR comments (when possible)
- Easy access to artifacts from PR comment
- Clear messaging if screenshot embedding fails
- Organized artifact naming with run numbers

## Testing

To verify the fix works:

1. **Create a PR with AutoQA tag**:
   ```markdown
   AutoQA
   1. Navigate to login page
   2. Enter credentials
   3. Verify dashboard appears
   ```

2. **Check PR Comment**:
   - Should show artifact link
   - May show embedded screenshot (if small enough)
   - Should have fallback link if embedding fails

3. **Check GitHub Actions**:
   - Go to Actions tab
   - Find the workflow run
   - Check "Artifacts" section
   - Download screenshots artifact

## Troubleshooting

### Screenshot Not Embedding?
- **Check file size**: Files >100KB won't embed directly
- **Check artifacts**: Always available via GitHub Actions artifacts link
- **Check logs**: Look for "Screenshot saved to:" messages in action logs

### Artifacts Not Appearing?
- **Check workflow**: Ensure artifact upload steps run (`if: always()`)
- **Check permissions**: Ensure action has write permissions
- **Check retention**: Artifacts kept for 30 days by default

### Path Resolution Issues?
- **Check ACTION_PATH**: Should be set to `.autoqa-action` directory
- **Check logs**: Look for path resolution warnings
- **Check working directory**: Ensure action runs from correct directory

## Environment Variables Used

- `ACTION_PATH`: Path to the AutoQA action workspace (`.autoqa-action/`)
- `GITHUB_WORKSPACE`: Path to the target repository workspace
- `GITHUB_RUN_ID`: GitHub Actions run ID (for artifacts link)
- `GITHUB_RUN_NUMBER`: GitHub Actions run number (for artifact naming)
- `TARGET_REPOSITORY`: Target repository full name (owner/repo)

## Files Modified

1. **action.yml**: Added artifact upload steps
2. **src/autoqa/reporter.py**: Enhanced screenshot resolution and PR comments
3. **src/agents/executor_agent.py**: Fixed screenshot save paths
4. **src/agents/executor_agent_fixed.py**: Fixed screenshot save paths

## Migration Notes

If you're using an older version of AutoQA:

1. **Update action.yml**: Pull latest version with artifact upload steps
2. **Update workflows**: No changes needed in consuming repositories
3. **Check permissions**: Ensure workflows have artifact write permissions
4. **Test**: Create a test PR to verify screenshots appear

## Future Enhancements

Potential improvements for future releases:

- [ ] Support for multiple screenshots per test
- [ ] Screenshot comparison (before/after)
- [ ] Video recording of test execution
- [ ] Screenshot annotations with failure points
- [ ] Direct GitHub API upload for larger screenshots
- [ ] Screenshot thumbnails in PR comment with lightbox

---

*Last Updated: November 2, 2025*
