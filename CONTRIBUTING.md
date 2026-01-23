# Contributing to fabric-cicd

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/fabric-cicd.git
   cd fabric-cicd
   ```
3. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
4. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

## Development Workflow

### 1. Create a Branch

Create a new branch for your feature or bugfix:

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, readable code following Python best practices
- Add comments where necessary
- Update documentation if you're changing functionality

### 3. Test Your Changes

If tests exist, run them:

```bash
pytest
```

Run linting:

```bash
black .
flake8 .
mypy .
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: description of your changes"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

This project follows standard Python conventions:

- **PEP 8** style guide
- **Black** for code formatting (line length: 100)
- **Type hints** where appropriate
- **Docstrings** for functions and classes

### Running Code Formatters

```bash
# Format code with Black
black .

# Check style with flake8
flake8 .

# Type checking with mypy
mypy .
```

## Testing

- Add tests for new features in the `tests/` directory
- Ensure all tests pass before submitting a PR
- Aim for good test coverage

## Documentation

- Update the README.md if you're adding new features
- Add docstrings to new functions and classes
- Update examples if applicable
- Keep the documentation clear and concise

## MCP Server Configuration

When modifying MCP server configuration:

1. Test the configuration locally first
2. Document any new environment variables in `.env.template`
3. Update `.mcp/README.md` with usage instructions
4. Ensure backward compatibility when possible

## GitHub Actions Workflows

When modifying CI/CD workflows:

1. Test workflow syntax using `act` or GitHub's workflow validator
2. Ensure workflows work across all supported Python versions
3. Document any new secrets required in the README
4. Keep workflows efficient and maintainable

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

## Feature Requests

Feature requests are welcome! Please:

- Check if the feature has already been requested
- Clearly describe the feature and its use case
- Explain why it would be valuable to the project

## Code Review Process

All submissions require review before merging:

1. A maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged

## Questions?

If you have questions about contributing:

- Open an issue on GitHub
- Refer to the README.md for project setup
- Check existing issues and PRs for similar discussions

Thank you for contributing! 🎉
