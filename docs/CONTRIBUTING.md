# Contributing to Driver Conversion Framework

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🤝 Ways to Contribute

- **Code:** Implement features, fix bugs, improve performance
- **Documentation:** Improve docs, add examples, fix typos
- **Testing:** Add tests, test on different hardware, report bugs
- **Device Support:** Add support for new device classes
- **Security:** Report vulnerabilities, improve security features
- **Legal:** Help with licensing, compliance research

## 📋 Getting Started

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/whats-a-script/TP-link-wifi-MT7927-reverse-engineer.git
cd TP-link-wifi-MT7927-reverse-engineer
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

4. **Install development tools:**
```bash
pip install pytest pytest-cov flake8 mypy black
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_analyzer.py
```

### Code Style

We use:
- **Black** for Python code formatting (max line length: 100)
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## 🔧 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clear, concise code
- Add docstrings to functions and classes
- Add type hints where possible
- Update documentation if needed

### 3. Add Tests

- Write unit tests for new features
- Ensure existing tests still pass
- Aim for >80% code coverage

### 4. Commit Changes

Use clear commit messages:
```bash
git commit -m "Add feature: description"
git commit -m "Fix: bug description"
git commit -m "Docs: update README"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📝 Pull Request Guidelines

### PR Title Format
- `feat: Add support for X`
- `fix: Resolve issue with Y`
- `docs: Update documentation for Z`
- `test: Add tests for W`
- `refactor: Improve code structure`

### PR Description Should Include
- **What:** Brief description of changes
- **Why:** Motivation and context
- **How:** Technical approach (if complex)
- **Testing:** How you tested the changes
- **Related Issues:** Link to related issues

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No new warnings from linters
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## 🧪 Testing Guidelines

### Unit Tests
- Test individual functions and classes
- Use mocks for external dependencies
- Name tests clearly: `test_<function>_<scenario>_<expected>`

```python
def test_analyzer_classify_driver_returns_correct_model():
    """Test that analyzer correctly identifies NDIS driver."""
    analyzer = DriverAnalyzer()
    result = analyzer.classify(mock_ndis_imports)
    assert result.model == DriverModel.NDIS_MINIPORT
```

### Integration Tests
- Test component interactions
- Use fixtures for test data
- Clean up resources after tests

### Hardware Tests
- Document required hardware
- Provide alternative test methods (VMs, mocks)
- Make hardware tests optional

## 🐛 Reporting Bugs

### Bug Report Should Include
- **Title:** Clear, concise description
- **Environment:** OS, kernel version, Python version
- **Steps to Reproduce:** Detailed steps
- **Expected Behavior:** What should happen
- **Actual Behavior:** What actually happens
- **Logs:** Relevant error messages or logs
- **Hardware:** Device info if hardware-related

### Security Vulnerabilities
**DO NOT** open public issues for security vulnerabilities.
Email security@[project].org (to be created)

## 💡 Feature Requests

- Check if feature already requested (search issues)
- Clearly describe the use case
- Explain why existing solutions don't work
- Be open to discussion and alternatives

## 📚 Documentation

### Documentation Standards
- Use Markdown for all documentation
- Include code examples where helpful
- Keep language clear and concise
- Update table of contents if needed

### Areas Needing Documentation
- API reference
- Architecture diagrams
- Tutorial guides
- Device-specific notes
- Troubleshooting guides

## 🏷️ Code Review Process

1. **Automated Checks:** CI must pass
2. **Maintainer Review:** At least one maintainer approval
3. **Community Feedback:** Consider feedback from community
4. **Final Approval:** Maintainer merges PR

### What Reviewers Look For
- Code quality and style
- Test coverage
- Documentation completeness
- Security considerations
- Legal compliance (for driver code)
- Performance impact

## 🎓 Learning Resources

### Linux Kernel Development
- [Linux Device Drivers (LDD3)](https://lwn.net/Kernel/LDD3/)
- [Kernel Newbies](https://kernelnewbies.org/)
- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/)

### Driver Development
- [Linux Wireless](https://wireless.wiki.kernel.org/)
- [USB Driver Development](https://www.kernel.org/doc/html/latest/driver-api/usb/index.html)
- [PCI Driver Development](https://www.kernel.org/doc/html/latest/PCI/pci.html)

### Reverse Engineering
- [Ghidra Documentation](https://ghidra-sre.org/)
- [Binary Analysis Course](https://maxkersten.nl/binary-analysis-course/)

## 📞 Community

- **GitHub Discussions:** For questions and discussions
- **Issues:** For bugs and feature requests
- **Email:** For private communications

## ⚖️ Legal Considerations

When contributing:
- Ensure you have rights to contribute code
- Do not contribute code from proprietary sources
- Respect vendor intellectual property
- Document information sources
- Follow clean-room design if necessary

See [LEGAL-COMPLIANCE.md](docs/LEGAL-COMPLIANCE.md) for details.

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Mentioned in relevant documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License (for framework) and GPLv2 (for kernel modules).

---

Thank you for contributing to open source driver development! 🎉
