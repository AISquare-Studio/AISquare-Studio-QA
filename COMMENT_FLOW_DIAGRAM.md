# 🔄 Comment Deduplication Flow

## How the Single Comment Fix Works

### Before Fix (Multiple Comments) ❌

```
PR #123 Timeline:

Commit 1 → Workflow Run #1
   ↓
   Creates Comment #1
   ┌─────────────────────────┐
   │ ✅ AutoQA Results       │
   │ Test: PASSED            │
   │ Screenshot: [link]      │
   └─────────────────────────┘

Commit 2 → Workflow Run #2
   ↓
   Creates Comment #2
   ┌─────────────────────────┐
   │ ✅ AutoQA Results       │
   │ Test: PASSED            │
   │ Screenshot: [link]      │
   └─────────────────────────┘

❌ Result: 2 comments (duplicate)
```

### After Fix (Single Comment) ✅

```
PR #123 Timeline:

Commit 1 → Workflow Run #1
   ↓
   Check for existing comments → None found
   ↓
   Creates Comment #1
   ┌─────────────────────────┐
   │ ✅ AutoQA Results       │
   │ Test: PASSED            │
   │ Screenshot: [link]      │
   │ <!-- marker -->         │
   └─────────────────────────┘

Commit 2 → Workflow Run #2
   ↓
   Check for existing comments → Found Comment #1
   ↓
   Updates Comment #1 (in place)
   ┌─────────────────────────┐
   │ ✅ AutoQA Results       │
   │ Test: PASSED            │
   │ Screenshot: [link]      │
   │ (edited) ← indicator    │
   │ <!-- marker -->         │
   └─────────────────────────┘

✅ Result: 1 comment (updated)
```

---

## Technical Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    AutoQA Action Execution                 │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│              Generate Test Results & Screenshots           │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│         reporter.create_pr_comment()                       │
│         Build comment body with results                    │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│         reporter._post_pr_comment()                        │
│         Smart comment posting logic                        │
└────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
         ┌──────────▼──────┐   ┌───▼──────────┐
         │ Find Existing   │   │ Create New   │
         │ Comment         │   │ Comment      │
         └──────────┬──────┘   └───┬──────────┘
                    │               │
         ┌──────────▼──────────────▼──────────┐
         │  _find_existing_autoqa_comment()   │
         │  GET /issues/{pr}/comments         │
         └──────────┬──────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │ Search for marker:  │
         │ <!-- AutoQA-...--> │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │ Found?              │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼────┐         ┌─────▼─────┐
    │ YES     │         │ NO        │
    │ Found   │         │ Not Found │
    └────┬────┘         └─────┬─────┘
         │                     │
    ┌────▼────────────┐   ┌───▼──────────────┐
    │ PATCH           │   │ POST             │
    │ /comments/{id}  │   │ /issues/{pr}/... │
    │ Update existing │   │ Create new       │
    └────┬────────────┘   └───┬──────────────┘
         │                     │
         └──────────┬──────────┘
                    │
              ┌─────▼─────┐
              │ Success!  │
              │ ✅ Done   │
              └───────────┘
```

---

## Code Flow

```python
# Entry Point
create_pr_comment(generation_result, execution_result, ...)
    │
    ├─> Build comment body with all results
    │   ├─ Status (pass/fail)
    │   ├─ Test steps
    │   ├─ Execution results
    │   ├─ Screenshots (embedded or linked)
    │   ├─ Artifacts link
    │   └─ Hidden marker: <!-- AutoQA-Comment-Marker -->
    │
    └─> _post_pr_comment(comment_body)
        │
        ├─> _find_existing_autoqa_comment()
        │   │
        │   ├─> GET /repos/{owner}/{repo}/issues/{pr}/comments
        │   │
        │   ├─> Loop through all comments
        │   │   ├─ Check: Contains "<!-- AutoQA-Comment-Marker -->"?
        │   │   │   └─ YES → Return comment_id
        │   │   ├─ Check: Contains "## AutoQA Test..." header?
        │   │   │   └─ YES → Return comment_id (legacy)
        │   │   └─ NO → Continue searching
        │   │
        │   └─> Return comment_id or None
        │
        ├─> If comment_id found:
        │   └─> PATCH /repos/{owner}/{repo}/issues/comments/{id}
        │       └─> Update existing comment
        │
        └─> If comment_id NOT found:
            └─> POST /repos/{owner}/{repo}/issues/{pr}/comments
                └─> Create new comment
```

---

## API Interaction Diagram

### Scenario 1: First Comment (Create)

```
AutoQA Action                 GitHub API
     │                             │
     ├─────── GET comments ───────>│
     │                             │
     │<─────── [] (empty) ─────────┤
     │                             │
     ├─────── POST comment ────────>│
     │         {body: "..."}        │
     │                             │
     │<─────── 201 Created ─────────┤
     │         {id: 123, ...}       │
     │                             │
     └─ ✅ Comment created
```

### Scenario 2: Update Existing Comment

```
AutoQA Action                 GitHub API
     │                             │
     ├─────── GET comments ───────>│
     │                             │
     │<─── [{id: 123, body:...}] ──┤
     │    (found existing)          │
     │                             │
     ├─ 🔍 Search for marker        │
     │   Found comment #123         │
     │                             │
     ├──── PATCH comment/123 ──────>│
     │      {body: "new..."}        │
     │                             │
     │<─────── 200 OK ──────────────┤
     │         {id: 123, ...}       │
     │                             │
     └─ ✅ Comment updated
```

---

## State Diagram

```
           ┌──────────────────┐
           │  Workflow Start  │
           └────────┬─────────┘
                    │
           ┌────────▼─────────┐
           │  Execute Tests   │
           └────────┬─────────┘
                    │
           ┌────────▼─────────┐
           │ Generate Results │
           └────────┬─────────┘
                    │
           ┌────────▼─────────┐
           │  Check for       │
           │  Existing        │
           │  Comment         │
           └────────┬─────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼────┐         ┌─────▼─────┐
    │ Found   │         │ Not Found │
    └────┬────┘         └─────┬─────┘
         │                     │
    ┌────▼─────────┐    ┌─────▼──────────┐
    │ Update Mode  │    │ Create Mode    │
    │              │    │                │
    │ PATCH API    │    │ POST API       │
    └────┬─────────┘    └─────┬──────────┘
         │                     │
         └──────────┬──────────┘
                    │
           ┌────────▼─────────┐
           │  Comment Posted  │
           │  or Updated      │
           └────────┬─────────┘
                    │
           ┌────────▼─────────┐
           │   Upload         │
           │   Artifacts      │
           └────────┬─────────┘
                    │
           ┌────────▼─────────┐
           │  Workflow Done   │
           │  ✅ Success      │
           └──────────────────┘
```

---

## Marker Implementation

### The Hidden Marker

```html
<!-- AutoQA-Comment-Marker -->
```

**Properties:**
- ✅ Invisible in rendered Markdown
- ✅ Preserved in API responses
- ✅ Unique to AutoQA comments
- ✅ Easy to search for
- ✅ No visual impact

### Where It Appears:

```markdown
## ✅ AutoQA Test Generation Results

**Status:** ✅ SUCCESS
**Test File:** `tests/generated/test_login.py`

### 📸 Screenshots
[... screenshot content ...]

### 🔗 Action Details
- Repository: owner/repo
- PR: #123

---
*🤖 This test was automatically generated by AutoQA*

<!-- AutoQA-Comment-Marker -->
```

### How It's Detected:

```python
for comment in all_pr_comments:
    if '<!-- AutoQA-Comment-Marker -->' in comment.body:
        return comment.id  # Found it!
```

---

## Benefits Summary

### Before:
```
❌ Multiple comments per PR
❌ Cluttered discussion thread
❌ Confusion about which is latest
❌ Manual cleanup required
```

### After:
```
✅ One comment per PR
✅ Clean discussion thread
✅ Always shows latest results
✅ Automatic management
✅ Edit history preserved
```

---

## Real-World Example

### PR Timeline:

```
Day 1, 10:00 AM - Initial commit
  └─> AutoQA runs
      └─> Creates comment with test results
          Status: ✅ PASSED

Day 1, 2:00 PM - Bug fix commit
  └─> AutoQA runs
      └─> UPDATES same comment
          Status: ✅ PASSED
          (edited)

Day 2, 9:00 AM - Feature addition
  └─> AutoQA runs
      └─> UPDATES same comment
          Status: ❌ FAILED (new test failed)
          (edited)

Day 2, 11:00 AM - Fix the test
  └─> AutoQA runs
      └─> UPDATES same comment
          Status: ✅ PASSED
          (edited)

Result: One comment, always current ✅
```

---

*This visual guide explains the single comment implementation in AutoQA*
