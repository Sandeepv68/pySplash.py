# Contributing to pySplash.py

Thanks for your interest in contributing to pySplash.py! This document provides guidelines and information for contributors.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```sh
   git clone https://github.com/<your-username>/pySplash.py.git
   cd pySplash.py
   ```
3. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

## Development Workflow

### Branching

- Create a feature branch from `master`:
  ```sh
  git checkout -b feature/your-feature-name
  ```

### Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```sh
# Check for lint issues
python -m ruff check .

# Auto-fix safe issues
python -m ruff check . --fix

# Check formatting
python -m ruff format --check .

# Auto-format
python -m ruff format .
```

### Running Tests

```sh
pytest tests/ -v
```

With coverage:

```sh
pytest tests/ -v --cov=pySplash --cov-report=term-missing
```

### Before Submitting

1. Run the linter: `python -m ruff check .`
2. Run the formatter: `python -m ruff format .`
3. Ensure all tests pass: `pytest tests/ -v`
4. Maintain or improve test coverage (minimum 80%)
5. Update documentation if adding/changing public API
6. Write clear commit messages

## Submitting Changes

1. Push your branch to your fork
2. Open a Pull Request against `master`
3. Describe what your changes do and why
4. Reference any related issues (e.g., "Closes #12")

## Reporting Bugs

Use the [bug report template](https://github.com/Sandeepv68/pySplash.py/issues/new?template=bug_report.md) when filing a bug. Include:

- Python version and OS
- pySplash.py version
- Minimal code to reproduce the issue
- Expected vs actual behavior

## Feature Requests

Use the [feature request template](https://github.com/Sandeepv68/pySplash.py/issues/new?template=feature_request.md). Describe the use case and how it benefits the project.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to its terms.

## License

By contributing to pySplash.py, you agree that your contributions will be licensed under the [MIT License](LICENSE).
