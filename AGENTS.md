# Repository Guidelines

## Project Structure & Module Organization
- `inventorybot/` holds the core bot code.
- Key modules: `entities.py` (data models), `parser.py` (command parsing), `service.py` (business logic), `vision.py` (image/AI integration), `settings.py` (config), and `infra/markdown_output.py` (Markdown/YAML output).
- `main.py` is the runtime entry point.
- Tests live next to the code as `inventorybot/test_*.py`.
- Documentation and config examples: `README.md`, `.env.example`.

## Build, Test, and Development Commands
- `poetry install` installs runtime + dev dependencies.
- `poetry run python main.py` runs the Telegram bot locally.
- `poetry run pytest` runs the test suite.
- `poetry run ruff check .` runs linting (and `--fix` for auto-fixes when safe).

## Coding Style & Naming Conventions
- Python 3.13+, 4-space indentation, and PEP 8 style.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Keep configuration in `settings.py` and environment variables rather than hardcoding values.

## Testing Guidelines
- Framework: `pytest`.
- Naming: files `test_*.py`, functions `test_*`.
- Add tests alongside the module you change in `inventorybot/` when introducing new behavior or fixing bugs.

## Commit & Pull Request Guidelines
- Commit messages follow Conventional Commits (observed types include `feat:` and `docs:`). Example: `feat: add allowed user IDs setting`.
- PRs should include a short summary, relevant context, and how you tested (e.g., `poetry run pytest`). Link related issues when applicable.

## Security & Configuration Tips
- Store secrets in `.env` and never commit real tokens.
- If you introduce new environment variables, update `.env.example` and document them in `README.md`.
