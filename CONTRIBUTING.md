# Contributing to souppy

Thank you for your interest in contributing to souppy! This document provides guidelines and information for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone the repo
git clone https://github.com/your-username/soup.git
cd soup/soup-oss/souppy

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Keep functions focused and concise
- Write docstrings for public functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage

```bash
pytest
pytest --cov=souppy
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure CI passes
4. Request review from maintainers

## Reporting Issues

- Use GitHub Issues
- Include reproduction steps
- Include Python version and OS
- Include error messages if applicable

## License

By contributing, you agree that your contributions will be licensed under the MPL-2.0 License.
