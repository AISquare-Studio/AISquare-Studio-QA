# AISquare Studio QA - Automated Testing with CrewAI + Playwright

A modern, AI-powered test automation framework that combines **CrewAI agents** with **Playwright** for intelligent web application testing.

## 🚀 Features

- **AI-Powered Test Generation**: CrewAI agents generate Playwright test code from natural language scenarios
- **Safe Code Execution**: AST-based validation ensures generated code is secure
- **Modern Browser Automation**: Playwright for reliable, fast cross-browser testing
- **Comprehensive Reporting**: Screenshots, traces, and detailed HTML reports
- **Minimal Setup**: Start testing with just valid/invalid login scenarios

## 🏗️ Project Structure

```
AISquare-Studio-QA/
├── src/
│   ├── agents/           # CrewAI agents (Planner, Executor)
│   ├── tools/           # Custom Playwright execution tools
│   └── crews/           # Main crew orchestration
├── config/
│   └── test_data.yaml   # Test scenarios and selectors
├── tests/
│   └── test_login.py    # Login functionality tests
├── reports/             # Test results and screenshots
├── run_login_tests.py   # Main test runner
└── setup_environment.py # Environment setup script
```

## 🛠️ Quick Setup

### 1. Environment Setup
```bash
# Run the automated setup
python setup_environment.py
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp env_template .env
# Edit .env with your staging URL and credentials
```

### 3. Install Dependencies (if not done by setup script)
```bash
pip install -r requirements.txt
playwright install chromium firefox webkit
```

## 🎯 Current Test Scenarios

### Login Tests
- ✅ **Valid Login**: Test successful authentication with correct credentials
- ❌ **Invalid Login**: Test failure handling with incorrect password

## 🚀 Running Tests

### Method 1: Using the Main Runner
```bash
python run_login_tests.py
```

### Method 2: Using Pytest
```bash
# Run all login tests
pytest tests/test_login.py -v

# Run specific test
pytest tests/test_login.py::TestLoginFunctionality::test_valid_login -v
```

### Method 3: Run Individual Scenarios
```python
from src.crews.qa_crew import QACrew

qa_crew = QACrew()
result = qa_crew.run_test_scenario('login', 'valid_login')
```

## 📊 Test Results

After running tests, you'll find:
- **Screenshots**: `reports/screenshots/` (success/failure/error captures)
- **Test Results**: `reports/test_results.json` (detailed execution data)
- **Console Output**: Real-time test progress and results

## 🔧 Configuration

### Environment Variables (.env)
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Staging Environment
STAGING_URL=https://your-staging-environment.com
STAGING_LOGIN_URL=https://your-staging-environment.com/login

# Test Credentials
VALID_EMAIL=test_user@example.com
VALID_PASSWORD=valid_password123
INVALID_PASSWORD=wrong_password

# Test Configuration
HEADLESS_MODE=false
BROWSER_TYPE=chromium
TIMEOUT=30000
```

### Test Scenarios (config/test_data.yaml)
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

1. **Planning Phase**: The Planner Agent reads test scenarios and generates Playwright code
2. **Validation Phase**: Generated code is validated for security and correctness
3. **Execution Phase**: The Executor Agent runs the validated code safely
4. **Reporting Phase**: Results, screenshots, and traces are collected

## 🔒 Security Features

- **AST Code Validation**: Prevents execution of malicious code
- **Restricted Imports**: Only allows safe Playwright-related imports
- **Sandboxed Execution**: Tests run in controlled environment
- **No File System Access**: Generated code cannot access local files

## 📈 Extending the Framework

### Adding New Test Scenarios
1. Update `config/test_data.yaml` with new scenarios
2. Add corresponding selectors if needed
3. Create new test methods in test files

### Adding New Test Types
1. Create new scenario sections in YAML
2. Extend the QACrew class with new methods
3. Add new test files in the `tests/` directory

## 🐛 Troubleshooting

### Common Issues

**Environment Setup**
```bash
# If setup fails, try manual installation
pip install --upgrade pip
pip install -r requirements.txt
playwright install --with-deps chromium
```

**OpenAI API Issues**
- Ensure your API key is valid and has sufficient credits
- Check that you're using the correct model name (gpt-4o)

**Playwright Issues**
- Ensure browsers are installed: `playwright install`
- For Linux: `playwright install-deps`

## 🎯 Development Roadmap

- [ ] Add signup functionality tests
- [ ] Implement self-healing selectors
- [ ] Add parallel test execution
- [ ] Create CI/CD integration
- [ ] Add visual regression testing
- [ ] Implement test data generation

---

**Built with ❤️ using CrewAI and Playwright**
