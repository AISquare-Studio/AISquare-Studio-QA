# 🚀 FE-REACT AutoQA Integration Guide

This guide will help you integrate AutoQA test generation into your FE-REACT repository.

## 📋 Prerequisites

- FE-REACT repository with appropriate permissions
- GitHub repository secrets configured
- Staging environment accessible for testing

## 🔧 Setup Steps

### 1. Repository Secrets Configuration

Add the following secrets to your FE-REACT repository (`Settings > Secrets and variables > Actions`):

#### Required Secrets:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

#### Staging Environment Secrets:
```
STAGING_URL=https://your-staging-url.com
STAGING_EMAIL=test@example.com
STAGING_PASSWORD=your-staging-password
```

### 2. Workflow File Setup

Copy the workflow file to your FE-REACT repository:

```bash
# In your FE-REACT repository
mkdir -p .github/workflows
cp fe-react-autoqa-workflow.yml .github/workflows/autoqa.yml
```

### 3. Package.json Script (Optional)

Add AutoQA test script to your `package.json`:

```json
{
  "scripts": {
    "test:autoqa": "playwright test tests/autoqa/",
    "test:autoqa:headed": "playwright test tests/autoqa/ --headed",
    "test:autoqa:debug": "playwright test tests/autoqa/ --debug"
  }
}
```

## 🤖 How to Use AutoQA

### 1. Create a Pull Request

Create a PR with AutoQA test steps in the description:

```markdown
## Feature: User Login Enhancement

This PR improves the user login experience.

AutoQA
1. Navigate to login page at "/login"
2. Enter valid email credentials
3. Enter valid password
4. Click login button
5. Verify successful login and dashboard redirect

### Changes Made
- Updated login form validation
- Added better error messages
- Improved loading states
```

### 2. Automatic Test Generation

The workflow will automatically:
- ✅ Detect the AutoQA tag in your PR
- ✅ Parse the numbered test steps
- ✅ Generate Playwright test code
- ✅ Execute tests on staging environment
- ✅ Commit generated tests to your repository
- ✅ Comment results back to the PR

### 3. Manual Trigger (Optional)

You can also trigger test generation manually:

1. Go to `Actions` tab in your repository
2. Select "🤖 AutoQA Test Generation" workflow
3. Click "Run workflow"
4. Enter the PR number
5. Click "Run workflow"

## 📁 Generated Files

Tests will be generated in:
```
tests/autoqa/
├── test_autoqa_login_001.py
├── test_autoqa_checkout_002.py
└── ...
```

## 🔧 Configuration Options

### Workflow Customization

Edit `.github/workflows/autoqa.yml` to customize:

```yaml
# Change test directory
test-directory: 'e2e/autoqa'

# Enable existing test execution
run-existing-tests: 'true'

# Custom git user
git-user-name: 'FE-REACT AutoQA Bot'
git-user-email: 'autoqa@yourcompany.com'
```

### Staging Environment

Update staging configuration in repository secrets:
- `STAGING_URL`: Your staging environment URL
- `STAGING_EMAIL`: Test user email
- `STAGING_PASSWORD`: Test user password

## 📊 Test Results

### Success Flow
```
✅ Test generation successful!
📁 Generated test file: tests/autoqa/test_autoqa_login_001.py
🧪 Test execution: PASSED ✅

### Next Steps
1. Review the generated test file
2. Adjust test steps if needed
3. Run tests locally: npm run test:autoqa
4. Commit and push the test file
```

### Failure Handling
```
❌ Test generation failed
Error: STAGING_URL is required but not provided

### Troubleshooting
1. Ensure your PR description contains "AutoQA" followed by numbered test steps
2. Check that all required secrets are configured
3. Verify the staging environment is accessible
```

## 📈 Memory & Coverage Stats

AutoQA tracks test results and source-module coverage over time via its **Memory Tracker**. This section explains where to find these stats for your frontend repository.

### Where Stats Are Stored

| Location | What You'll Find |
|----------|-----------------|
| `reports/autoqa_memory.json` | Persistent JSON file with per-test results, history, and coverage gaps |
| PR comments | Summary table posted automatically when `report_on_pr` is enabled |
| GitHub Actions run summary | Step summary attached to each workflow run |
| GitHub Actions artifacts | Full HTML/JSON reports and screenshots (retained for 14 days) |

### Viewing Stats on Pull Requests

When memory tracking is enabled (default), AutoQA posts a **Memory Report** comment on each PR that includes:

- **Test Results Summary** — total tests, pass/fail/error/skip counts
- **Coverage Percentage** — how many source modules have corresponding test files
- **Failing Tests** — list of failing or erroring tests with error messages
- **Missing Tests** — source modules that lack a test file, with suggested file names

This is controlled by the `report_on_pr: true` setting in `config/autoqa_config.yaml`:

```yaml
autoqa:
  memory:
    enabled: true
    report_on_pr: true      # Post memory report as PR comment
    update_on_ci: true      # Update memory on CI runs
```

### Viewing Stats in GitHub Actions

1. Go to the **Actions** tab in your frontend repository
2. Select the AutoQA workflow run you want to inspect
3. Open the **run summary** — the memory report is included in the step summary
4. Click **Artifacts** to download full reports (`report.html`, `autoqa_memory.json`, screenshots)

### Viewing Stats Locally

Use the `qa_runner.py` CLI to generate memory and coverage stats from your local machine:

```bash
# Scan tests and source files for coverage gaps (no test execution)
python qa_runner.py --memory-scan

# Run tests and update the memory file with results
python qa_runner.py --memory-update

# Print a markdown report from the current memory file
python qa_runner.py --memory-report
```

**Example output from `--memory-report`:**

```
📋 AutoQA Memory Report

📊 Test Results Summary
| Metric        | Count |
|---------------|-------|
| Total Tests   | 12    |
| ✅ Passed     | 10    |
| ❌ Failed     | 1     |
| ⏭️ Skipped    | 1     |

🔍 Test Coverage
| Metric           | Value |
|------------------|-------|
| Source Modules    | 30    |
| Covered           | 12    |
| Uncovered         | 18    |
| Coverage          | 40.0% |
```

### Memory File Location

The memory file is saved at `reports/autoqa_memory.json` inside your repository (configurable via `memory_file` in `config/autoqa_config.yaml`). It contains:

- **test_entries** — per-test status, last run timestamp, duration, error messages, and history (up to 10 runs by default, configurable via `history_limit` in `config/autoqa_config.yaml`)
- **coverage_gaps** — list of source modules and whether they have a corresponding test file
- **summary** — aggregate counts (total tests, status breakdown, coverage percentage)

> **Tip:** Commit `reports/autoqa_memory.json` to your repository so the memory persists across CI runs and team members can view the latest stats.

---

## 🎯 Best Practices

### 1. Writing Effective AutoQA Steps

**Good Example:**
```
AutoQA
1. Navigate to login page at "/login"
2. Enter email "test@example.com" in email field
3. Enter password "password123" in password field
4. Click the "Sign In" button
5. Verify redirect to dashboard page
6. Verify welcome message appears
```

**Avoid:**
```
AutoQA
1. Test login
2. Check if it works
3. Make sure user can access dashboard
```

### 2. Test Step Guidelines

- ✅ Be specific about URLs, selectors, and expected outcomes
- ✅ Use clear action verbs (Navigate, Enter, Click, Verify)
- ✅ Include expected text and element descriptions
- ✅ Test both positive and negative scenarios
- ❌ Avoid vague descriptions
- ❌ Don't assume complex business logic

### 3. Repository Organization

```
your-fe-react-repo/
├── .github/workflows/
│   └── autoqa.yml
├── tests/autoqa/
│   ├── test_autoqa_login_001.py
│   └── test_autoqa_checkout_002.py
├── package.json
└── playwright.config.js
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "AutoQA tag not found"
- Ensure your PR description contains the word "AutoQA"
- Check that test steps are numbered (1., 2., 3., etc.)

#### 2. "OPENAI_API_KEY not found"
- Add the secret to repository settings
- Verify the secret name matches exactly

#### 3. "Test execution failed"
- Check staging environment accessibility
- Verify staging credentials are correct
- Review generated test selectors

#### 4. "No test files generated"
- Check workflow logs for detailed error messages
- Ensure repository has write permissions
- Verify test directory configuration

### Debug Workflow

1. Check workflow logs in GitHub Actions
2. Review generated test files for syntax issues
3. Test staging environment manually
4. Validate repository secrets configuration

## 🚀 Advanced Usage

### Custom Selectors

You can provide custom selectors in your test steps:

```
AutoQA
1. Navigate to login page at "/login"
2. Enter email in field with selector "input[data-testid='email']"
3. Enter password in field with selector "input[data-testid='password']"
4. Click button with selector "button[data-testid='login-submit']"
5. Verify dashboard loads with selector ".dashboard-container"
```

### Multi-Environment Testing

Configure different staging environments:

```yaml
# staging.yml
staging-url: ${{ secrets.STAGING_URL }}

# development.yml  
staging-url: ${{ secrets.DEV_URL }}

# production-like.yml
staging-url: ${{ secrets.PROD_LIKE_URL }}
```

## 📞 Support

For issues and questions:
- 📧 Create an issue in [AISquare-Studio-QA](https://github.com/AISquare-Studio/AISquare-Studio-QA/issues)
- 📖 Check the [main documentation](../README.md)
- 🔧 Review [action usage guide](../docs/ACTION_USAGE.md)