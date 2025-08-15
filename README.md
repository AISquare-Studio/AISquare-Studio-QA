# AISquare S## 🚀 Quick Start

### 1. Setup ## 🚀 Quick Start

### 1. Setup Environment
Create a `.env` file in the project root with your staging configuration:## 📊 Reporting

After every test execution, comprehensive reports are automatically generated:
- `reports/html/` - Interactive HTML test reports with screenshots
- `reports/json/` - Machine-readable test results for CI/CD integration
- `reports/screenshots/` - Visual evidence of test execution and failures

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
STAGING_LOGIN_URL=https://your-staging.com/login
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
STAGING_LOGIN_URL=https://your-staging.com/login
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

🚀 **Production-ready automated testing framework** powered by **CrewAI** + **Playwright** + **OpenAI GPT-4** for intelligent login/signup functionality testing.

## ✨ Features

- 🤖 **AI-Powered Test Generation**: CrewAI agents generate Playwright test code using natural language scenarios
- 🔒 **Security-First**: AST-based code validation ensures generated code is safe to execute
- 🌐 **Cross-Browser Testing**: Supports Chromium, Firefox, and WebKit
- 📊 **Comprehensive Reporting**: HTML reports, JSON outputs, and screenshot capture
- 🔧 **Easy Setup**: Interactive configuration wizard for staging environments

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
├── config/                # ⚙️ Configuration files
│   └── test_data.yaml     # Test scenarios and selectors
├── src/                   # 🤖 AI framework components
│   ├── agents/            # CrewAI agents for test planning and execution
│   ├── crews/             # AI crew orchestration
│   └── tools/             # Playwright execution tools
├── tests/                 # 🧪 Pytest test suites
│   ├── test_login.py      # Login functionality tests
│   └── conftest.py        # Pytest configuration
├── scripts/               # 🛠️ Utility scripts and tools
│   ├── README.md          # Scripts documentation
│   ├── setup_staging.py   # Environment setup wizard
│   ├── test_staging_connection.py
│   └── ...                # Additional utility scripts
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
1. Run `python qa_runner.py --help-detailed`
2. Review generated reports in `reports/` directory
3. Check .env configuration matches your staging environment
4. Verify OpenAI API key is valid and has sufficient credits

---

**Built with ❤️ by AISquare Studio**
