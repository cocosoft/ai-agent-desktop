# Contributing to AI Agent Desktop

Thank you for your interest in contributing to AI Agent Desktop! We welcome contributions from the community and are grateful for your help in making this project better.

## 🎯 How to Contribute

### Reporting Bugs
If you find a bug, please create an issue with the following information:
- **Description**: Clear and concise description of the bug
- **Steps to Reproduce**: Step-by-step instructions to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots to help explain
- **Environment**: OS, Python version, and other relevant details

### Suggesting Features
We welcome feature suggestions! Please create an issue with:
- **Feature Description**: Clear description of the proposed feature
- **Use Case**: How this feature would be used
- **Alternatives**: Any alternative solutions you've considered
- **Additional Context**: Any other context or screenshots

### Code Contributions
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for your changes
5. **Ensure all tests pass**
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

## 🛠️ Development Setup

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Steps
1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/cocosoft/ai-agent-desktop.git
   cd ai-agent-desktop
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up development environment**:
   ```bash
   # Install development dependencies
   pip install pytest pytest-cov black flake8 mypy
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## 📝 Code Standards

### Python Code Style
We follow PEP 8 style guidelines. Please use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

### Code Quality
- Write clear, readable code with meaningful variable names
- Add docstrings for all public functions and classes
- Include type hints for function parameters and return values
- Write unit tests for new functionality

### Testing
- Ensure all tests pass before submitting a PR
- Add tests for new features and bug fixes
- Maintain or improve test coverage

### Documentation
- Update documentation for new features
- Keep API documentation current
- Add comments for complex logic

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

### Test Structure
- **Unit Tests**: `tests/unit/` - Test individual components
- **Integration Tests**: `tests/integration/` - Test component interactions
- **Performance Tests**: `tests/performance/` - Test performance characteristics

## 📋 Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Follow coding standards** and ensure all tests pass
3. **Update documentation** if you're changing functionality
4. **Add tests** for new features or bug fixes
5. **Ensure the test suite passes**
6. **Make sure your code lints** (run `black` and `flake8`)
7. **Issue that pull request!**

### PR Review Criteria
- **Code Quality**: Clean, readable, and well-documented
- **Functionality**: Works as expected and handles edge cases
- **Testing**: Includes appropriate tests
- **Documentation**: Updated documentation if needed
- **Performance**: No significant performance regressions

## 🏷️ Commit Message Convention

We follow conventional commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or modifying tests
- **chore**: Maintenance tasks

### Examples:
```
feat(agent): add agent template system
fix(ui): resolve memory leak in main window
docs(readme): update installation instructions
```

## 🐛 Issue Labels

We use the following labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 📞 Getting Help

- **Documentation**: Check the [docs](docs/) directory
- **Issues**: Search existing issues or create a new one
- **Discussion**: Join our community discussions

## 🙏 Recognition

All contributors will be recognized in our:
- **Contributors list** in the README
- **Release notes** for significant contributions
- **Project documentation**

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for contributing to AI Agent Desktop! 🚀

**AI Agent Desktop Team**
