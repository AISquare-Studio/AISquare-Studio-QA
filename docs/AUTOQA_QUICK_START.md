# AutoQA Quick Start Guide (Phase 1)

## 🚀 How to Use the New AutoQA Format

### Basic Template

Copy this into your PR description:

````markdown
```autoqa
flow_name: your_test_name_here
tier: B
area: your_area
```
1. Your first test step here
2. Your second test step here
3. Add verification steps
4. Keep going as needed
````

### Real Example

````markdown
```autoqa
flow_name: user_login_success
tier: A
area: auth
```
1. Navigate to login page at "/login"
2. Enter email "test@example.com" in email field
3. Enter password "testpass123" in password field
4. Click the "Login" button
5. Verify user is redirected to dashboard page
6. Verify welcome message "Welcome back!" is displayed
````

---

## 📋 Field Reference

| Field | Required? | Valid Values | Example | Default |
|-------|-----------|--------------|---------|---------|
| `flow_name` | ✅ Yes | snake_case, max 50 chars | `user_login_success` | - |
| `tier` | ❌ No | `A`, `B`, `C` | `A` | `B` |
| `area` | ❌ No | snake_case, max 30 chars | `auth` | `general` |

---

## 🎯 Tier Guidelines

### Tier A - Critical (40 tests max)
**Use for:** Core functionality that breaks the app
- Login/Signup
- Payments/Checkout
- Data persistence
- API authentication

### Tier B - Important (40 tests max)
**Use for:** Major features and common flows
- Forms and validation
- Navigation
- CRUD operations
- Search functionality

### Tier C - Optional (20 tests max)
**Use for:** Nice-to-have features
- Tooltips
- Animations
- Edge cases
- Minor UI elements

---

## ✍️ Writing Good Steps

### DO ✅

```
1. Navigate to login page at "/login"
2. Enter email "user@test.com" in email field
3. Click the "Login" button
4. Verify success message "Login successful" appears
5. Verify user is redirected to "/dashboard"
```

### DON'T ❌

```
1. Go to login
2. Login with credentials
3. Check if logged in
```

**Why?**
- ✅ Specific URLs and paths
- ✅ Exact text in quotes
- ✅ Clear element descriptions
- ✅ Verification steps

---

## 📁 Where Your Test Will Live

**Pattern:** `tests/autoqa/{tier}/{area}/test_{flow_name}.py`

### Examples:

```
flow_name: user_login_success
tier: A
area: auth
→ tests/autoqa/A/auth/test_user_login_success.py

flow_name: contact_form_validation
tier: B
area: forms
→ tests/autoqa/B/forms/test_contact_form_validation.py

flow_name: tooltip_display
tier: C
(no area specified)
→ tests/autoqa/C/general/test_tooltip_display.py
```

---

## 🔄 What Happens After You Submit

1. **AutoQA detects** your metadata block
2. **Validates** metadata and steps
3. **Computes ETag** for idempotency
4. **Generates** test code with AI
5. **Executes** test on staging
6. **Commits** test file to your repo
7. **Posts** PR comment with results

---

## ✅ Pre-Submit Checklist

- [ ] Used triple backticks with `autoqa` language
- [ ] Set appropriate tier (A/B/C)
- [ ] Added area if applicable
- [ ] Steps are numbered (1, 2, 3...)
- [ ] Each step is specific and clear
- [ ] Included verification steps
- [ ] Text content is in "quotes"
- [ ] URLs are specified like "/login"

---

## 🐛 Common Issues

### Issue: "No AutoQA metadata block found"
**Solution:** Make sure you use triple backticks with `autoqa`:
````markdown
```autoqa
flow_name: test_name
tier: B
```
````

### Issue: "Invalid tier value"
**Solution:** Tier must be uppercase A, B, or C (or omit for default B)

### Issue: "flow_name too long"
**Solution:** Keep flow_name under 50 characters

### Issue: "Missing required field: flow_name"
**Solution:** flow_name is required, make sure it's in your metadata block

---

## 💡 Tips & Tricks

### Tip 1: Use Descriptive Flow Names
- ✅ `user_login_with_remember_me`
- ❌ `test1`

### Tip 2: Group Related Tests by Area
- `area: auth` for login, signup, password reset
- `area: commerce` for cart, checkout, payments
- `area: studio` for AI features

### Tip 3: Tier by Business Impact
- If it breaks → Tier A
- If users complain → Tier B
- If nobody notices → Tier C

### Tip 4: One Flow Per PR
Only include ONE `autoqa` block per PR (not multiple)

---

## 📊 PR Comment Preview

After submission, you'll see:

```markdown
## ✅ AutoQA Test Generation Results

**Status:** ✅ SUCCESS
**Generated Test:** `tests/autoqa/A/auth/test_user_login_success.py`

### 📊 Test Metadata
- **Flow Name:** `user_login_success`
- **Tier:** `A`
- **Area:** `auth`
- **ETag:** `a1b2c3d4...` (idempotency hash)

### 📋 Test Steps Generated
[Your steps here]

### 🧪 Test Execution Results
- **Generated Test:** ✅ PASSED
- **Execution Time:** 12.34s

### 📁 Generated Artifacts
[Links to screenshots and reports]
```

---

## 🎓 More Examples

### Example 1: Simple Login (Tier A, with area)
````markdown
```autoqa
flow_name: basic_user_login
tier: A
area: auth
```
1. Navigate to "/login"
2. Enter email "test@example.com"
3. Enter password "password123"
4. Click "Login" button
5. Verify redirect to "/dashboard"
````

### Example 2: Form Validation (Tier B, with area)
````markdown
```autoqa
flow_name: contact_form_empty_validation
tier: B
area: forms
```
1. Navigate to "/contact"
2. Click "Submit" button without filling fields
3. Verify error "Email is required" appears
4. Verify error "Message is required" appears
````

### Example 3: Dashboard Widget (Tier C, no area)
````markdown
```autoqa
flow_name: dashboard_widget_toggle
tier: C
```
1. Navigate to "/dashboard"
2. Click "Hide Widgets" button
3. Verify widgets section is hidden
4. Click "Show Widgets" button
5. Verify widgets section is visible
````

---

## 📚 Additional Resources

- **Full Template:** `examples/PR_TEMPLATE_WITH_AUTOQA.md`
- **Policy Details:** `.github/autoqa-policy.yml`
- **Configuration:** `config/autoqa_config.yaml`

---

**Questions?** Tag @TahirRabia in your PR for help!
