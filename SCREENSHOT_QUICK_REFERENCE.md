# 📸 Screenshot Quick Reference

## How to Access AutoQA Screenshots

### 1. **In PR Comments** (Automatic) ✅
- Small screenshots (<100KB) are **embedded directly**
- Large screenshots show a **link to artifacts**
- Always includes a **"View All Artifacts & Screenshots"** link

### 2. **In GitHub Actions Artifacts** (Always Available) 📦
```
1. Go to your repository's Actions tab
2. Click on the AutoQA workflow run
3. Scroll to "Artifacts" section at the bottom
4. Download:
   - autoqa-screenshots-{run-number}
   - autoqa-reports-{run-number}
```

### 3. **Retention Period** ⏰
- Screenshots kept for **30 days**
- Accessible even after PR is merged/closed
- Downloadable as ZIP archives

## Screenshot Types

| Type | Filename Pattern | When Captured |
|------|-----------------|---------------|
| Success | `test_completion_YYYYMMDD_HHMMSS.png` | Test passes successfully |
| Error | `test_error_YYYYMMDD_HHMMSS.png` | Test fails or throws error |

## Troubleshooting

### ❓ "Screenshot not embedded in PR comment?"
**✅ Solution**: Check the artifacts link - large screenshots aren't embedded but are always uploaded

### ❓ "Can't find screenshots?"
**✅ Solution**: 
1. Go to Actions tab
2. Find your workflow run
3. Look for "Artifacts" section
4. Download the screenshot artifact

### ❓ "Artifacts expired?"
**✅ Solution**: Screenshots are kept for 30 days. Re-run the workflow to regenerate them.

### ❓ "Need higher resolution?"
**✅ Solution**: Screenshots are full-page captures at 1280x720 resolution. Check the downloaded artifact for full quality.

## PR Comment Example

```markdown
## ✅ AutoQA Test Generation Results

**Status:** ✅ SUCCESS
**Generated Test:** `tests/generated/test_login.py`

### 📁 Generated Artifacts
- 📄 **Test File:** `tests/generated/test_login.py`
- 📦 **[View All Artifacts & Screenshots](https://github.com/owner/repo/actions/runs/12345)**

### 📸 Success Screenshot
![Success Screenshot](data:image/png;base64,iVBORw0KG...)
```

## Screenshot Locations in Artifacts

When you download the artifact ZIP, you'll find:

```
autoqa-screenshots-123/
├── test_completion_20251102_143022.png  (Success screenshot)
└── test_error_20251102_143022.png       (Error screenshot, if failed)
```

## Best Practices

### ✅ DO:
- Check PR comments first for quick preview
- Download artifacts for detailed analysis
- Use screenshots to verify visual state
- Keep screenshots for debugging purposes

### ❌ DON'T:
- Expect large screenshots to embed in comments
- Rely on screenshots older than 30 days
- Share screenshot URLs externally (they expire)

## Need More Help?

- **Detailed Documentation**: [docs/SCREENSHOT_FIX.md](SCREENSHOT_FIX.md)
- **Full Usage Guide**: [docs/ACTION_USAGE.md](ACTION_USAGE.md)
- **Changelog**: [CHANGELOG_SCREENSHOT_FIX.md](CHANGELOG_SCREENSHOT_FIX.md)

---
*Last Updated: November 2, 2025*
