# 🔄 Update: Single Comment Fix

**Date**: November 2, 2025  
**Issue**: Multiple comments appearing on PR (duplicate comments)  
**Status**: ✅ FIXED

---

## Problem

Users were seeing **2 comments** on their PRs instead of 1:
1. One comment from the AutoQA action itself
2. Another comment from workflow steps in user's workflow file

This caused:
- Duplicate information
- Cluttered PR threads
- Confusion about which comment to reference

## Solution

Implemented **comment deduplication** by:

1. **Adding a unique marker** to AutoQA comments:
   ```markdown
   <!-- AutoQA-Comment-Marker -->
   ```
   This hidden HTML comment acts as an identifier.

2. **Checking for existing comments** before posting:
   - The action now searches for previous AutoQA comments
   - Uses the hidden marker to identify them
   - Updates existing comment instead of creating new one

3. **Update vs Create logic**:
   ```python
   if existing_comment_found:
       PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}
   else:
       POST /repos/{owner}/{repo}/issues/{issue_number}/comments
   ```

## Changes Made

### File: `src/autoqa/reporter.py`

#### 1. Updated `_post_pr_comment()` method:
- Now checks for existing AutoQA comments first
- Updates existing comment if found
- Creates new comment only if none exists
- Provides clear logging for both scenarios

#### 2. Added `_find_existing_autoqa_comment()` method:
- Fetches all PR comments
- Searches for AutoQA marker
- Returns comment ID if found
- Handles errors gracefully

#### 3. Added hidden marker to comment body:
- Appended `<!-- AutoQA-Comment-Marker -->` to all comments
- Hidden from users but detectable by API
- Allows reliable comment identification

## How It Works Now

### First Run (No existing comment):
```
1. AutoQA executes → Generates results
2. Reporter checks PR comments → None found
3. Creates NEW comment with marker
4. ✅ One comment appears
```

### Subsequent Runs (Comment exists):
```
1. AutoQA executes → Generates new results
2. Reporter checks PR comments → Finds AutoQA comment
3. Updates EXISTING comment with new results
4. ✅ Same comment updated, no duplicates
```

## Visual Comparison

### ❌ BEFORE (Multiple Comments)
```
PR #123 Comments:
┌────────────────────────────────────┐
│ Comment #1 (AutoQA - First Run)    │
│ ✅ Test passed                      │
│ Screenshot: [link]                 │
└────────────────────────────────────┘
┌────────────────────────────────────┐
│ Comment #2 (AutoQA - Second Run)   │
│ ✅ Test passed                      │
│ Screenshot: [link]                 │
└────────────────────────────────────┘
❌ Duplicates!
```

### ✅ AFTER (Single Comment)
```
PR #123 Comments:
┌────────────────────────────────────┐
│ Comment #1 (AutoQA - Updated)      │
│ ✅ Test passed                      │
│ Screenshot: [link]                 │
│ (Edited) ← Updated in place        │
└────────────────────────────────────┘
✅ Single, updated comment!
```

## Benefits

### For Users:
- ✅ **Clean PR threads** - Only one AutoQA comment
- ✅ **Latest results** - Comment always shows most recent run
- ✅ **Edit history** - GitHub shows "edited" marker
- ✅ **No manual cleanup** - Automatic deduplication

### For Workflows:
- ✅ **Idempotent** - Multiple runs don't create duplicates
- ✅ **Reliable** - Uses hidden marker for identification
- ✅ **Backward compatible** - Still finds old comments without marker
- ✅ **Error tolerant** - Falls back gracefully if update fails

## Technical Details

### API Calls Made:

#### Finding Existing Comment:
```http
GET /repos/{owner}/{repo}/issues/{pr_number}/comments
Authorization: token {github_token}
```

#### Creating New Comment:
```http
POST /repos/{owner}/{repo}/issues/{pr_number}/comments
Authorization: token {github_token}
Content-Type: application/json

{
  "body": "## ✅ AutoQA Test Generation Results\n..."
}
```

#### Updating Existing Comment:
```http
PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}
Authorization: token {github_token}
Content-Type: application/json

{
  "body": "## ✅ AutoQA Test Generation Results\n..."
}
```

### Comment Marker:

The hidden marker is a standard HTML comment that:
- ✅ Is invisible in rendered markdown
- ✅ Is preserved in API responses
- ✅ Is unique to AutoQA comments
- ✅ Is search-friendly for identification

```html
<!-- AutoQA-Comment-Marker -->
```

### Fallback Logic:

For backward compatibility with existing comments:
1. **Primary**: Search for `<!-- AutoQA-Comment-Marker -->`
2. **Fallback**: Search for header text pattern
3. **Safety**: If both fail, create new comment

## Testing

### Verification Steps:

1. **First PR push**:
   - ✅ One comment created
   - ✅ Contains marker in source

2. **Second PR push** (same PR):
   - ✅ No new comment created
   - ✅ Existing comment updated
   - ✅ Shows "edited" indicator

3. **Third PR push** (same PR):
   - ✅ Still one comment
   - ✅ Latest results shown
   - ✅ Previous results replaced

### Expected Logs:

**First run:**
```
🔍 No existing AutoQA comment found
📝 Creating new AutoQA comment
✅ PR comment posted successfully
```

**Subsequent runs:**
```
🔍 Found existing AutoQA comment: 123456789
📝 Updating existing AutoQA comment (ID: 123456789)
✅ PR comment updated successfully
```

## Migration

### No Action Required! 🎉

This fix is **automatically applied** when using:
```yaml
uses: AISquare-Studio/AISquare-Studio-QA@main
```

### For Users with Custom Workflows:

If you have custom workflow steps that post comments, you may want to:

**Option 1: Remove custom comment step** (Recommended)
The action now handles all commenting automatically.

**Option 2: Keep custom step**
The action will still update its own comment, your custom step will create a separate comment.

## Troubleshooting

### "Still seeing duplicate comments?"

**Check 1**: Are they both from AutoQA?
- Look for the marker in comment source
- AutoQA comments will update, others won't

**Check 2**: Custom workflow steps?
- Check your `.github/workflows/*.yml` files
- Look for `github-script` or API calls posting comments
- Consider removing if redundant

**Check 3**: Different PR numbers?
- Each PR gets its own comment
- Multiple PRs = Multiple comments (expected)

### "Comment not updating?"

**Check 1**: Permissions
- Ensure `GITHUB_TOKEN` has write permissions
- Check workflow permissions in settings

**Check 2**: API rate limits
- Look for rate limit errors in logs
- Wait and retry if needed

**Check 3**: Comment deleted
- If comment was manually deleted, new one will be created
- This is expected behavior

## Code Reference

### Key Methods:

```python
# Main entry point
def create_pr_comment(...)
    └─> _post_pr_comment()
        ├─> _find_existing_autoqa_comment()
        │   └─> Returns comment_id or None
        ├─> If found: PATCH (update)
        └─> If not found: POST (create)

# Finding existing comments
def _find_existing_autoqa_comment(...)
    ├─> GET all PR comments
    ├─> Search for marker
    └─> Return first match or None
```

## Future Enhancements

Potential improvements:
- [ ] Track comment edit history
- [ ] Show diff between runs
- [ ] Collapse previous results
- [ ] Add "Show History" button
- [ ] Automatic cleanup of very old comments

---

## Summary

**Problem**: Multiple duplicate comments  
**Solution**: Update existing comment instead of creating new one  
**Impact**: Clean, single AutoQA comment per PR  
**Status**: ✅ Fixed and deployed  

*Users will see this fix automatically on next PR!*

---

*Updated: November 2, 2025*
