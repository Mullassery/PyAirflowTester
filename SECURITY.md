# Security Policy

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please report it responsibly.

**Do not open public GitHub issues for security vulnerabilities.**

Instead, please email: mullassery@gmail.com with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

We will acknowledge receipt within 48 hours and aim to provide an update within 5 business days.

## Security Measures

PyAirflowTester implements the following security measures:

### Code Security
- Type hints throughout codebase
- Input validation at system boundaries
- Proper error handling without information leakage
- No hardcoded credentials or secrets
- Regular dependency updates

### Data Security
- No unnecessary data storage
- Secure defaults for configuration
- Audit trail logging for compliance
- Support for TLS/SSL connections

### Development Security
- Pre-commit hooks for code quality
- Static analysis with Ruff and Clippy
- Type checking with mypy
- Comprehensive test coverage (85%+)
- Dependency scanning and updates

### Access Control
- Support for RBAC (Role-Based Access Control)
- Ownership tracking for all nodes
- SLA enforcement
- Audit logging

## Supported Versions

- Python 3.10+
- Airflow 2.0+
- dbt 1.0+

## Dependency Management

We regularly review and update dependencies. To update:

```bash
pip install --upgrade pyairflowtester
```

## Compliance

PyAirflowTester is designed with compliance in mind:

- GDPR compliance features (data retention, deletion)
- HIPAA-ready (audit logging, encryption support)
- SOX compliance support (change tracking, audit trail)
- CCPA support (data minimization)

## Security Best Practices

When using PyAirflowTester:

1. Keep dependencies updated
2. Use environment variables for sensitive data
3. Enable audit logging
4. Regularly review access logs
5. Set appropriate SLAs
6. Monitor alert configurations

## Reporting Other Issues

For non-security issues, use GitHub Issues: https://github.com/Mullassery/PyAirflowTester/issues

## Security Update Notifications

We recommend:
- Watching the GitHub repository for releases
- Subscribing to PyPI notifications
- Enabling security alerts in GitHub

## Third-Party Security

PyAirflowTester uses the following security-related libraries:
- Click for CLI argument parsing
- Pydantic for input validation
- SQLAlchemy for database access
- OpenTelemetry for observability

All dependencies are regularly audited and updated.

## Contact

For security matters: mullassery@gmail.com

Thank you for helping us keep PyAirflowTester secure.
