# React Repository Integration Guide

This guide shows how to integrate the AISquare AutoQA GitHub Action into your React frontend repository for automated test generation.

## Prerequisites

1. **React Repository**: Your frontend React application repository
2. **GitHub Repository Secrets**: Access to configure repository secrets
3. **OpenAI API Key**: Valid OpenAI API key with credits

## Step 1: Configure Repository Secrets

In your React repository, add the required secrets:

1. Go to your React repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-`)
   
   - **Name**: `STAGING_URL`
   - **Value**: Your staging environment URL (e.g., `https://your-staging-app.vercel.app`)

## Step 2: Create GitHub Workflow

Create `.github/workflows/autoqa.yml` in your React repository:

```yaml
name: AutoQA Test Generation
on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout React Repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - name: Generate AutoQA Tests
        uses: AISquare-Studio/AISquare-Studio-QA@setup-playwright
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          staging-url: ${{ secrets.STAGING_URL }}
          target-repo-path: '.'
          git-user-name: 'AutoQA Bot'
          git-user-email: 'rabia.tahirr@opengrowth.com'
```

## Step 3: Configure Staging Environment

### Option A: Vercel Deployment (Recommended)

1. **Connect Vercel to your React repo**:
   ```bash
   # In your React repository
   npm install -g vercel
   vercel login
   vercel --prod
   ```

2. **Update workflow with Vercel URL**:
   Add to your repository secrets:
   ```
   STAGING_URL=https://your-app-name.vercel.app
   ```

### Option B: Netlify Deployment

1. **Connect Netlify to your React repo**
2. **Add Netlify URL to repository secrets**:
   ```
   STAGING_URL=https://your-app-name.netlify.app
   ```

### Option C: Custom Staging Server

```
STAGING_URL=https://staging.yourcompany.com
```

## Step 4: Create Your First AutoQA Test

In your PR description, add AutoQA tags to generate tests. Both formats are supported:

**New Format (Recommended)**:
```markdown
## AutoQA Test Cases

### Login Flow Test
AutoQA:login-flow
1. Navigate to login page at "/login"
2. Enter valid email "user@example.com"
3. Enter valid password "password123"
4. Click login button
5. Verify user is redirected to dashboard at "/dashboard"
6. Verify welcome message is displayed

### Shopping Cart Test
AutoQA:cart-functionality
1. Navigate to products page at "/products"
2. Click "Add to Cart" on first product
3. Verify cart icon shows count of 1
4. Click cart icon to open cart
5. Verify product is listed in cart
6. Click "Remove" button
7. Verify cart is empty
```

**Legacy Format (Also Supported)**:
```markdown
## AutoQA Test Cases

AutoQA
1. Navigate to login page at "/login"
2. Enter valid email "user@example.com"
3. Enter valid password "password123"
4. Click login button
5. Verify user is redirected to dashboard at "/dashboard"
```

## Step 5: Understanding Generated Tests

After creating a PR with AutoQA tags, the action will:

1. **Parse** your PR description for AutoQA tags
2. **Generate** Playwright test files using AI
3. **Execute** tests against your staging environment
4. **Commit** test files to your repository

Generated files will be placed in:
```
tests/generated/
├── login-flow_20250821_123456.spec.js
├── cart-functionality_20250821_123456.spec.js
└── metadata/
    ├── login-flow_20250821_123456.json
    └── cart-functionality_20250821_123456.json
```

## Step 6: React-Specific Configuration

### For Create React App

Add to your `package.json`:
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

### For Next.js

Create `playwright.config.js`:
```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/generated',
  use: {
    baseURL: 'http://localhost:3000',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});
```

### For Vite

Create `playwright.config.js`:
```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/generated',
  use: {
    baseURL: 'http://localhost:5173',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
});
```

## Step 7: Advanced Configuration

### Custom AutoQA Configuration

Create `.autoqa/config.yaml` in your React repository:

```yaml
# AutoQA Configuration for React App
test_framework: 'playwright'
browser: 'chromium'
viewport:
  width: 1280
  height: 720
timeouts:
  default: 30000
  navigation: 60000
selectors:
  strategy: 'data-testid'  # Prefer data-testid selectors
  fallback: 'css'
react:
  # React-specific settings
  wait_for_hydration: true
  detect_react_router: true
  component_testing: false
```

### Custom Test Templates

Create `.autoqa/templates/react-component.template`:

```javascript
import { test, expect } from '@playwright/test';

test.describe('{{scenario_name}}', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for React hydration
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('{{test_name}}', async ({ page }) => {
    {{generated_steps}}
  });
});
```

## Step 8: Testing Your Integration

1. **Create a test PR** with AutoQA tags
2. **Monitor the Actions tab** in your repository
3. **Check generated test files** in `tests/generated/`
4. **Review test execution reports**

### Sample PR for Testing

```markdown
# Test PR: AutoQA Integration

This PR tests the AutoQA integration.

## AutoQA Test Cases

### Homepage Loading Test
AutoQA:homepage-basic
1. Navigate to homepage at "/"
2. Verify page title contains "Your App Name"
3. Verify main navigation is visible
4. Verify footer is present
```

## Troubleshooting

### Common Issues

**Tests not generating?**
- Check `OPENAI_API_KEY` secret is configured
- Verify AutoQA tags are properly formatted
- Check GitHub Actions logs for errors

**Tests failing on staging?**
- Verify staging URL is accessible
- Check if staging environment is running
- Ensure test selectors match your React components

**Generated tests not working locally?**
- Install Playwright: `npx playwright install`
- Update base URL in `playwright.config.js`
- Check React development server is running

### React Component Best Practices

**Use data-testid attributes**:
```jsx
function LoginButton() {
  return (
    <button 
      data-testid="login-button"
      onClick={handleLogin}
    >
      Login
    </button>
  );
}
```

**Avoid relying on text content**:
```jsx
// Good
<button data-testid="submit-button">Submit</button>

// Avoid
<button>Submit</button>  // Text might change
```

## Next Steps

1. **Integrate AutoQA** into your development workflow
2. **Train your team** on AutoQA tag syntax
3. **Customize templates** for your specific React patterns
4. **Set up test reports** in your CI/CD pipeline

## Support

For issues or questions:
- Check the [main documentation](./ACTION_USAGE.md)
- Review GitHub Actions logs
- Open an issue in the AISquare-Studio-QA repository