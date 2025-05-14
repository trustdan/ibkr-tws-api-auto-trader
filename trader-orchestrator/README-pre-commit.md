# Pre-commit Hooks Setup

This project uses pre-commit hooks to ensure code quality and consistency.

## Installation

1. Install the development dependencies using Poetry:
   ```bash
   cd trader-orchestrator
   poetry install
   ```

2. Install the pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Usage

The hooks will run automatically when you commit changes. To manually run the hooks on all files:

```bash
poetry run pre-commit run --all-files
```

## Configured Hooks

- **black**: Code formatter
- **isort**: Import sorter (configured to be compatible with black)
- **flake8**: Linter with flake8-bugbear for additional checks

## Skipping Hooks

To bypass pre-commit hooks in exceptional cases:

```bash
git commit -m "Your message" --no-verify
```

However, this is discouraged as our CI pipeline still enforces these checks.

## Troubleshooting

If hooks need to be updated:

```bash
poetry run pre-commit autoupdate
```

For hook-specific issues, please refer to the documentation for that tool. 