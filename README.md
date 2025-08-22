# AISquare S## 🚀 Quick Start

### 1. Setup ## 🚀 How It Works

### **For Repository Owners**
1. **Add the GitHub Action** to your repository workflow
2. **Configure staging secrets** (login URL, credentials, OpenAI API key)
3. **Your developers use AutoQA tags** in PR descriptions

### **For Developers**
1. **Write test steps** in natural language in PR descriptions:
   ```markdown
   AutoQA
   1. Navigate to user profile page
   2. Update email address
   3. Save changes
   4. Verify email updated successfully
   ```
2. **Create pull request** - tests generate automatically
3. **Review generated tests** committed to your repository
4. **Tests execute on every future PR** as part of your test suite

### **AI Process**
1. **AutoQA Detection**: Parses PR descriptions for AutoQA tags
2. **CrewAI Generation**: Planner Agent converts steps to Playwright code  
3. **Security Validation**: AST parser ensures code safety
4. **Staging Execution**: Tests run against staging environment
5. **Test Persistence**: Successful tests commit to repository
6. **Suite Execution**: All tests (existing + generated) run together## 📊 Reporting

After every test execution, comprehensive reports are automatically generated:
- `reports/html/` - Interactive HTML test reports with screenshots
- `reports/json/` - Machine-readable test results for CI/CD integration
- `reports/screenshots/` - Visual evidence of test execution and failures

### CI/CD Integration
- 🤖 **Automated on PR**: Tests run automatically on every pull request
- 💬 **PR Comments**: Results posted directly in GitHub PR comments
- 📁 **Artifact Upload**: Reports downloadable from GitHub Actions
- 🛡️ **Status Checks**: Pass/fail status for branch protection

Reports include:
- ✅ Test execution summary and results
- 📸 Screenshots of browser interactions
- ⏱️ Detailed timing and performance metrics
- 🔍 AI-generated code and validation resultsash
# Copy the template and fill in your values
cp env.template .env
```

Edit the `.env` file with your actual values:
```bash
# Required: Your staging environment
STAGING_LOGIN_URL=https://stg-home.aisquare.studio/login
STAGING_EMAIL=your-test-email@domain.com
STAGING_PASSWORD=your-test-password

# Required: OpenAI API key for AI test generation
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Browser settings
HEADLESS_MODE=true
DEFAULT_TIMEOUT=30000
```

### 2. Run Tests
```bash
# Run all AI-powered tests against staging
python qa_runner.py

# Get detailed help
python qa_runner.py --help-detailed
```a `.env` file in the project root with your staging configuration:

```bash
# Copy the template and fill in your values
cp env.template .env
```

Edit the `.env` file with your actual values:
```bash
# Required: Your staging environment
STAGING_LOGIN_URL=https://stg-home.aisquare.studio/login
STAGING_EMAIL=your-test-email@domain.com
STAGING_PASSWORD=your-test-password

# Required: OpenAI API key for AI test generation
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Browser settings
HEADLESS_MODE=true
DEFAULT_TIMEOUT=30000
```

### 2. Run Tests
```bash
# Run all AI-powered tests against staging
python qa_runner.py

# Get detailed help
python qa_runner.py --help-detailed
```ed Test Automation

# AISquare Studio QA - AI-Powered Test Automation Action

🚀 **GitHub Action for automated testing** powered by **CrewAI** + **Playwright** + **OpenAI GPT-4** for intelligent test generation and execution.

## 🎯 Use This Action in Your Repository

### **Quick Setup**

1. **Add to your workflow** (`.github/workflows/autoqa.yml`):

```yaml
name: AutoQA Test Generation

on:
  pull_request:
    types: [opened, synchronize, edited]

jobs:
  autoqa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          
      - name: 🤖 Generate and Execute Tests
        uses: AISquare-Studio/AISquare-Studio-QA@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          staging-login-url: ${{ secrets.STAGING_LOGIN_URL }}
          staging-email: ${{ secrets.STAGING_EMAIL }}
          staging-password: ${{ secrets.STAGING_PASSWORD }}
```

2. **Configure secrets** in your repository settings
3. **Use AutoQA tag** in PR descriptions:

```markdown
AutoQA
1. Navigate to login page at "/login"
2. Enter valid credentials  
3. Click login button
4. Verify dashboard appears
```

4. **Watch tests generate automatically!** 🎉

📖 **[Complete Usage Guide](docs/ACTION_USAGE.md)**

## ✨ Features

- 🤖 **AI-Powered Test Generation**: CrewAI agents generate Playwright test code from natural language in PR descriptions
- 🔒 **Security-First**: AST-based code validation ensures generated code is safe to execute
- 📁 **Cross-Repository**: Deploy as GitHub Action, use in any repository to generate and store tests
- 🌐 **Staging Environment Testing**: Automated execution against staging environments
- 📊 **Comprehensive Reporting**: Test results, screenshots, and execution logs
- � **Test Persistence**: Generated tests commit directly to your repository
- 🔧 **Zero Configuration**: Works out-of-the-box with minimal setup

## � Quick Start

### 1. Setup Environment
```bash
# Configure staging environment (interactive)
python qa_runner.py --setup

# Test connectivity
python qa_runner.py --test-connection
```

### 2. Run Tests
```bash
# Run all AI-powered tests against staging
python qa_runner.py

# Get detailed help
python qa_runner.py --help-detailed
```

## 📁 Project Structure

```
AISquare-Studio-QA/
├── qa_runner.py           # 🎯 Main test runner (production entry point)
├── .github/               # 🔄 CI/CD workflows and templates
│   ├── workflows/         # GitHub Actions workflows
│   │   ├── pr-qa-checks.yml        # Main PR QA automation
│   │   └── setup-qa-environment.yml # Environment validation
│   └── PULL_REQUEST_TEMPLATE.md    # PR template with QA section
├── config/                # ⚙️ Configuration files
│   └── test_data.yaml     # Test scenarios and selectors
├── src/                   # 🤖 AI framework components
│   ├── agents/            # CrewAI agents for test planning and execution
│   ├── crews/             # AI crew orchestration
│   └── tools/             # Playwright execution tools
├── tests/                 # 🧪 Pytest test suites
│   ├── test_login.py      # Login functionality tests
│   └── conftest.py        # Pytest configuration
├── docs/                  # 📚 Documentation
│   ├── WEEK1_DEMO_PLAN.md      # Week 1 demo execution guide
│   ├── SETUP_GUIDE.md          # CI/CD setup instructions
│   ├── WEEK1_DEMO_CHECKLIST.md # Demo preparation checklist
│   └── SECURITY.md             # Security & compliance guide
├── scripts/               # 🛠️ Utility scripts and tools
│   └── README.md          # Scripts documentation
├── reports/               # 📊 Test reports and screenshots
└── requirements.txt       # 📦 Python dependencies
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file (copy from `env.template`):

```bash
# Staging Environment
STAGING_LOGIN_URL=https://your-staging.com/login
STAGING_EMAIL=test@example.com
STAGING_PASSWORD=your_password

# OpenAI Configuration (required)
OPENAI_API_KEY=your_openai_api_key

# Browser Settings
HEADLESS_MODE=true
BROWSER_TYPE=chromium
```

### Test Scenarios
Configure test scenarios in `config/test_data.yaml`:

```yaml
test_scenarios:
  login:
    valid_login:
      name: "Valid Login Test"
      description: "Test successful login with correct credentials"
      steps:
        - "Navigate to the login page"
        - "Enter valid email address"
        - "Enter valid password"
        - "Click login button"
        - "Verify successful login"
```

## 🤖 How It Works

1. **AI Planning**: CrewAI Planner Agent generates Playwright test code from natural language scenarios
2. **Security Validation**: AST parser validates generated code for security compliance
3. **Test Execution**: Playwright Executor runs validated code against staging environment
4. **Result Collection**: Framework captures screenshots, logs, and generates comprehensive reports

## � Reporting

After test execution, find reports in:
- `reports/html/` - Interactive HTML test reports
- `reports/screenshots/` - Visual evidence of test execution
- `reports/json/` - Machine-readable test results

## 🔧 Advanced Usage

### Custom Test Scenarios
1. Add scenarios to `config/test_data.yaml`
2. Define page selectors in the `selectors` section
3. Run tests with `python qa_runner.py`

### Debugging
```bash
# Run with visible browser
export HEADLESS_MODE=false && python qa_runner.py
```

# Check individual scripts
python scripts/test_staging_direct.py
```

### CI/CD Integration
```bash
# Set environment variables
export OPENAI_API_KEY=your_key
export STAGING_LOGIN_URL=https://staging.com/login

# Run tests
python qa_runner.py
```

## 🛠️ Development

### Adding New Test Types
1. Create new scenarios in `config/test_data.yaml`
2. Add corresponding selectors
3. Create test methods in `tests/`

### Extending AI Agents
- Modify `src/agents/planner_agent.py` for code generation logic
- Update `src/agents/executor_agent.py` for execution handling
- Enhance `src/crews/qa_crew.py` for orchestration

## 📦 Dependencies

Core requirements:
- **Python 3.11+**
- **CrewAI** - AI agent framework
- **Playwright** - Browser automation
- **OpenAI** - GPT-4 API for code generation
- **Pytest** - Testing framework

Install all dependencies:
```bash
pip install -r requirements.txt
playwright install
```

## 🔒 Security

- **Code Validation**: All AI-generated code is validated using AST parsing
- **Restricted Imports**: Only safe Playwright imports are allowed
- **Sandboxed Execution**: Tests run in isolated browser contexts
- **No File Access**: Generated code cannot perform file operations

## 🤝 Contributing

1. Follow existing code structure and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure security validation passes

## 📄 License

[Your License Here]

## 🆘 Support

For help and troubleshooting:
1. **CI/CD Setup**: See [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)
2. **Week 1 Demo**: See [`docs/WEEK1_DEMO_PLAN.md`](docs/WEEK1_DEMO_PLAN.md)
3. **Security Guide**: See [`docs/SECURITY.md`](docs/SECURITY.md)
4. Run `python qa_runner.py --help-detailed` for local testing
5. Review generated reports in `reports/` directory
6. Check .env configuration matches your staging environment
7. Verify OpenAI API key is valid and has sufficient credits

### 🎯 Week 1 Demo Ready!
This framework is **production-ready** for Week 1 CI/CD demonstration with:
- ✅ Complete GitHub Actions workflows
- ✅ Automated PR comments and status checks  
- ✅ Comprehensive security and compliance
- ✅ Professional documentation and setup guides

---

**Built with ❤️ by AISquare Studio**
