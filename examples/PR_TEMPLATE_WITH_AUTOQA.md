# Pull Request Template with AutoQA

## Description
Brief description of the changes in this PR.

## Changes Made
- [ ] List your changes here
- [ ] Add checkboxes as needed

---

## 🤖 AutoQA Test Generation

Use the fenced metadata block format below to automatically generate and execute tests for your changes:

### ✅ Example 1: User Authentication Flow (Tier A - Critical)

```autoqa
flow_name: user_login_success
tier: A
area: auth
```
1. Navigate to login page at "/login"
2. Enter email "test@example.com" in email field
3. Enter password "testpassword" in password field
4. Click the "Login" button
5. Verify user is redirected to dashboard page
6. Verify welcome message "Welcome back!" is displayed

---

### ✅ Example 2: Form Validation (Tier B - Important)

```autoqa
flow_name: contact_form_validation
tier: B
area: forms
```
1. Navigate to contact form at "/contact"
2. Click submit button without filling any fields
3. Verify error message "Email is required" appears
4. Enter invalid email "notanemail"
5. Verify error message "Please enter a valid email" appears
6. Enter valid email "user@example.com"
7. Verify error message disappears

---

### ✅ Example 3: Shopping Cart (Tier B - Important)

```autoqa
flow_name: add_remove_cart_items
tier: B
area: commerce
```
1. Navigate to products page at "/products"
2. Click "Add to Cart" button on first product
3. Verify cart badge shows count of "1"
4. Click cart icon to open cart modal
5. Verify product appears in cart with correct name and price
6. Click "Remove" button for the product
7. Verify cart is empty and shows "Your cart is empty"

---

### ✅ Example 4: Dashboard Navigation (Tier C - Optional, no area)

```autoqa
flow_name: dashboard_sidebar_navigation
tier: C
```
1. Navigate to dashboard at "/dashboard"
2. Click "Settings" in sidebar menu
3. Verify settings page loads with heading "User Settings"
4. Click "Profile" tab
5. Verify profile form is visible

---

## 📋 AutoQA Metadata Reference

### Required Fields

| Field | Description | Format | Example |
|-------|-------------|--------|---------|
| `flow_name` | Unique identifier for this test flow | snake_case, max 50 chars | `user_login_success` |
| `tier` | Test priority tier | `A`, `B`, or `C` | `A` |

### Optional Fields

| Field | Description | Format | Example |
|-------|-------------|--------|---------|
| `area` | Feature area/module | snake_case, max 30 chars | `auth`, `commerce`, `studio` |

### Tier Definitions

- **Tier A (Critical)**: Core functionality that breaks the app if it fails (e.g., login, signup, payments)
  - Quota: 40 tests per repo
- **Tier B (Important)**: Major features and common user flows (e.g., forms, navigation, CRUD)
  - Quota: 40 tests per repo
- **Tier C (Optional)**: Nice-to-have features and edge cases (e.g., tooltips, animations)
  - Quota: 20 tests per repo

**Total Quota: 100 curated tests per repository**

---

## ✍️ Writing Effective Test Steps

### Best Practices

1. **Be Specific**: Use exact text, URLs, and selectors
   - ✅ Good: `Navigate to login page at "/login"`
   - ❌ Bad: `Go to the login screen`

2. **Use Quotes**: Wrap UI text in double quotes
   - ✅ Good: `Verify error message "Email is required" appears`
   - ❌ Bad: `Verify error message Email is required appears`

3. **Include Verifications**: Always verify important outcomes
   - ✅ Good: `Click "Submit" button` → `Verify success message "Form submitted!" appears`
   - ❌ Bad: `Click "Submit" button` (no verification)

4. **Number Steps**: Keep steps sequential and logical (1, 2, 3...)

5. **One Action Per Step**: Don't combine multiple actions
   - ✅ Good: 
     - `Enter email "user@test.com"`
     - `Enter password "pass123"`
   - ❌ Bad: 
     - `Enter email and password`

### React-Specific Tips

- Use `data-testid` attributes in your components
- Reference components by their test IDs when possible
- Include React Router navigation paths (e.g., `/dashboard`, `/profile`)
- Test both desktop and mobile viewports when relevant

---

## 🔍 Validation Rules

AutoQA will validate your metadata:

- ✅ `flow_name` is required, snake_case, max 50 characters
- ✅ `tier` is required, must be `A`, `B`, or `C` (defaults to `B` if omitted)
- ✅ `area` is optional, snake_case, max 30 characters (defaults to `general`)
- ✅ At least 1 test step is required

**Validation errors will be reported in PR comments with clear fix instructions.**

---

## 📁 Generated Test Files

Tests will be committed to your repository following this structure:

```
tests/autoqa/
├── A/
│   ├── auth/
│   │   └── test_user_login_success.py
│   └── commerce/
│       └── test_checkout_flow.py
├── B/
│   ├── forms/
│   │   └── test_contact_form_validation.py
│   └── general/
│       └── test_add_remove_cart_items.py
└── C/
    └── general/
        └── test_dashboard_sidebar_navigation.py
```

Each generated file includes:
- `# AutoQA-Generated` header (for edit policy enforcement)
- ISO8601 timestamp with timezone
- Flow name, tier, area, and ETag (idempotency hash)
- All test steps as comments
- Pytest markers: `@pytest.mark.autoqa`, `@pytest.mark.tier_a`, `@pytest.mark.area_auth`

---

## 🔄 Idempotency & Updates

AutoQA computes an **ETag** (hash) from your metadata and steps:
- Same metadata + steps = **same ETag** → **no regeneration** (idempotent)
- Changed metadata or steps = **new ETag** → **regenerate test**

This prevents unnecessary test churn and preserves your review history.

---

## ✅ Testing Checklist

Before submitting your PR:

- [ ] AutoQA metadata block is properly formatted (fenced with triple backticks)
- [ ] `flow_name` is descriptive and follows snake_case
- [ ] `tier` is set appropriately (A for critical, B for important, C for optional)
- [ ] `area` is specified if applicable (optional)
- [ ] Test steps are clear, specific, and numbered
- [ ] Each step has verification steps where appropriate
- [ ] Staging environment is accessible for test execution
- [ ] Components have `data-testid` attributes (for React apps)

---

## 📚 Additional Resources

- **Policy**: See `.github/autoqa-policy.yml` for complete rules
- **Configuration**: See `config/autoqa_config.yaml` in the AutoQA action repo
- **Documentation**: See `docs/ACTION_USAGE.md` for detailed usage

---

**Note**: Tests will be automatically generated and executed against the staging environment when this PR is created or updated. Results will be posted as a PR comment with screenshots and execution logs.