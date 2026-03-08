# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

We take the security of AISquare Studio AutoQA seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to **security@aisquare.studio**.

Include the following information in your report:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Affected versions** (or commit SHAs)
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)

### What to Expect

- **Acknowledgment:** We will acknowledge receipt of your report within **48 hours**.
- **Assessment:** We will investigate and provide an initial assessment within **5 business days**.
- **Resolution:** We aim to release a fix within **30 days** of confirming the vulnerability.
- **Disclosure:** We will coordinate with you on the timing of public disclosure.

### Security Considerations for This Action

AISquare Studio AutoQA executes AI-generated code against staging environments. The following security measures are in place:

- **AST-based code validation** prevents dangerous constructs (`eval`, `exec`, `open`, `subprocess`)
- **Import allowlist** restricts imports to safe modules (`playwright.sync_api`, `time`, `datetime`, `re`)
- **Function call blocklist** prevents access to system-level functions
- **Sandboxed execution** runs generated tests in isolated contexts

If you discover a way to bypass these protections, please report it immediately using the process above.

### Scope

The following are in scope for security reports:

- Bypasses of the AST validation or import allowlist
- Injection vulnerabilities in PR body parsing
- Token or credential exposure in logs or artifacts
- Unauthorized access to repositories or environments
- Vulnerabilities in dependencies used by this action

### Out of Scope

- Vulnerabilities in the staging environment being tested (report those to the staging environment owner)
- Issues with GitHub Actions platform itself (report those to [GitHub Security](https://github.com/security))
- Social engineering attacks

## Security Best Practices for Users

When using AISquare Studio AutoQA:

1. **Use dedicated staging environments** — never point this action at production
2. **Use repository secrets** for all credentials (`OPENAI_API_KEY`, `STAGING_PASSWORD`, etc.)
3. **Review generated tests** before merging to your main branch
4. **Restrict workflow permissions** to the minimum required
5. **Enable branch protection** on your main branch
