# 🚀 AISquare Studio AutoQA - Usage Guide

## 📖 How to Use This Action in Your Repository

### **1. Setup in Your Repository**

Create a workflow file in your repository:

**`.github/workflows/autoqa.yml`**
```yaml
name: AutoQA Test Generation

on:
  pull_request:
    types: [opened, synchronize, edited]

jobs:
  autoqa:
    name: 🤖 Generate and Execute Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: 📋 Checkout Repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0
      
      - name: 🤖 Run AutoQA
        uses: AISquare-Studio/AISquare-Studio-QA@main
        with:
          target-repo-path: '.'
          git-user-name: 'AutoQA Bot'
          git-user-email: 'rabia.tahirr@opengrowth.com'
          test-directory: 'tests/generated'
      
      - name: 📊 Upload Test Reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: autoqa-reports
          path: |
            tests/generated/
            reports/
          retention-days: 30
```

### **2. Configure Repository Secrets**

Add these secrets to your repository (`Settings → Secrets and variables → Actions`):

```
OPENAI_API_KEY=sk-your-openai-api-key-here
STAGING_URL=https://your-staging-environment.com
```

**Note**: Both the OpenAI API key and staging URL are automatically accessed from repository secrets for security.

### **3. Use AutoQA in Pull Requests**

Add the AutoQA tag to your PR descriptions:

```markdown
## Feature: Enhanced User Dashboard

This PR adds new dashboard functionality.

AutoQA
1. Navigate to login page
2. Enter valid credentials
3. Click login button
4. Verify dashboard loads
5. Check welcome message appears
6. Verify navigation menu is visible

## Technical Details
- Updated dashboard components
- Added responsive design
```

### **4. What Happens Automatically**

1. **Detection**: Action detects AutoQA tag in PR description
2. **Parsing**: Extracts test steps from numbered list
3. **Generation**: CrewAI generates Playwright test code
4. **Validation**: AST validation ensures code safety
5. **Execution**: Test runs on staging environment
6. **Persistence**: Successful test commits to your repository
7. **Suite Run**: All tests execute together
8. **Reporting**: Results appear in GitHub Actions and PR comments

### **5. Generated Test Structure**

Tests will be created in your repository:

```
your-repository/
├── tests/
│   └── autoQA/
│       ├── __init__.py
│       ├── test_autoqa_login_20250821_1430.py
│       ├── test_autoqa_dashboard_20250821_1445.py
│       └── test_autoqa_navigation_20250821_1500.py
```

Each test file includes:
- Full metadata about generation source
- Properly formatted Playwright test code
- pytest compatibility
- Standalone execution capability

### **6. Example Generated Test**

```python
"""
AutoQA Generated Test
=====================

Generated: 2025-08-21T14:30:00
Source: AutoQA PR Description
Steps: 6
Scenario Type: dashboard

Test Steps:
1. Navigate to login page
2. Enter valid credentials
3. Click login button
4. Verify dashboard loads
5. Check welcome message appears
6. Verify navigation menu is visible
"""

import pytest
from playwright.sync_api import sync_playwright

class TestAutoQA:
    @pytest.mark.autoqa
    @pytest.mark.generated
    def test_autoqa_scenario(self):
        config = {
            'login_url': 'https://staging.example.com/login',
            'email': 'test@staging.com',
            'password': 'password123',
            'headless': True,
            'timeout': 30000
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config['headless'])
            page = browser.new_page()
            
            try:
                # Navigate to login page
                page.goto(config['login_url'])
                page.wait_for_load_state('networkidle')
                
                # Enter valid credentials
                page.fill('input[name="email"]', config['email'])
                page.fill('input[name="password"]', config['password'])
                
                # Click login button
                page.click('button[type="submit"]')
                page.wait_for_timeout(5000)
                
                # Verify dashboard loads
                page.wait_for_selector('.dashboard', timeout=10000)
                assert '/dashboard' in page.url
                
                # Check welcome message appears
                welcome_message = page.locator('.welcome-message')
                assert welcome_message.is_visible()
                
                # Verify navigation menu is visible
                nav_menu = page.locator('nav.main-navigation')
                assert nav_menu.is_visible()
                
            finally:
                browser.close()
```

### **7. Action Outputs**

The action provides these outputs for use in subsequent steps:

```yaml
- name: 🤖 Run AutoQA
  id: autoqa
  uses: AISquare-Studio/AISquare-Studio-QA@main
  # ... inputs ...

- name: 📊 Check Results
  run: |
    echo "Test Generated: ${{ steps.autoqa.outputs.test-generated }}"
    echo "Test File: ${{ steps.autoqa.outputs.test-file-path }}"
    echo "Results: ${{ steps.autoqa.outputs.test-results }}"
```

Available outputs:
- `test-generated`: "true" or "false"
- `test-file-path`: Path to generated test file
- `test-results`: JSON string of execution results
- `suite-results`: JSON string of full suite results

### **8. Advanced Configuration**

Customize action behavior with additional inputs:

```yaml
- name: 🤖 Run AutoQA (Advanced)
  uses: AISquare-Studio/AISquare-Studio-QA@main
  with:
    # Repository configuration
    target-repo-path: '.'
    
    # Optional customization
    git-user-name: 'AutoQA Bot'
    git-user-email: 'rabia.tahirr@opengrowth.com'
    test-directory: 'tests/qa-generated'        # Custom directory
    target-branch: ${{ github.head_ref }}       # Explicit branch
```

### **9. Best Practices**

#### **Writing AutoQA Steps**
- Use clear, actionable language
- Include verification steps
- Keep steps focused and specific
- Use numbered lists (1., 2., 3., etc.)

#### **Good Example:**
```
AutoQA
1. Navigate to user profile page
2. Click edit profile button
3. Update email address field
4. Click save changes button
5. Verify success message appears
6. Verify email address updated in profile
```

#### **Avoid:**
```
AutoQA
- Test the profile page
- Make sure it works
- Check everything is good
```

### **10. Troubleshooting**

#### **Common Issues**

**Action not triggering?**
- Ensure AutoQA tag is properly formatted
- Check that PR targets a branch with the workflow
- Verify workflow file is in `.github/workflows/`

**Test generation failing?**
- Check OpenAI API key is valid and has credits (automatically accessed from `OPENAI_API_KEY` repository secret)
- Verify AutoQA steps are numbered and clear
- Review GitHub Actions logs for detailed errors

**Test execution failing?**
- Verify staging environment is accessible
- Check staging credentials are correct
- Ensure staging site matches expected selectors

**No tests committed?**
- Check repository permissions for GitHub token
- Verify branch is not protected against direct commits
- Review commit errors in GitHub Actions logs

#### **Getting Help**

1. Check GitHub Actions logs for detailed error messages
2. Review generated test files for issues
3. Verify all required secrets are configured
4. Ensure staging environment is stable and accessible

### **11. Repository Requirements**

To use this action, your repository needs:

- ✅ GitHub Actions enabled
- ✅ Repository secrets configured
- ✅ Staging environment for testing
- ✅ Basic test directory structure (created automatically)
- ✅ Branch permissions allowing commits (not required for main branch)

### **12. Security & Compliance**

- 🔒 All secrets are masked in GitHub Actions logs
- 🔒 Generated code is validated with AST parsing
- 🔒 Execution is sandboxed and isolated
- 🔒 No production data or credentials used
- 🔒 Tests only run against staging environments

---

**🎉 You're ready to use AISquare Studio AutoQA in your repository!**

Start by creating a PR with AutoQA steps and watch the magic happen. 🚀