# Contributing to hellqvio86.unifi

Thank you for your interest in contributing to the `hellqvio86.unifi` Ansible collection!

## Development Guidelines

All code contributions should adhere to the quality standards defined in [agents.md](agents.md):

- **Strict Typing**: All Python code in `plugins/` must use type hints for function arguments and return types.
- **Code Style & Linting**: Code must pass `ruff check .`, `ansible-lint`, and version consistency checks cleanly (`make lint`).
- **Unit Testing**: Every module must have corresponding unit tests in `tests/unit/` using `pytest` and `unittest.mock`.
- **License**: Contributions are licensed under the MIT license (see `LICENSE.md`). Ensure module file headers reflect `# MIT License (see LICENSE.md)`.

## Local Development Workflow

1. Clone the repository:
   ```bash
   git clone https://github.com/hellqvio86/ansible-collection-unifi.git
   cd ansible-collection-unifi
   ```

2. Set up the development virtual environment:
   ```bash
   make venv
   ```

3. Run the test suite:
   ```bash
   make test
   # or run pytest directly:
   .venv/bin/pytest
   ```

4. Run linting:
   ```bash
   make lint
   ```

5. Format code:
   ```bash
   make format
   ```

6. Verify build:
   ```bash
   make smoke-test
   ```

## Pull Request Process

1. Create a feature or bugfix branch from `main`.
2. Make your changes with clear, descriptive commit messages.
3. Ensure all tests (`make test`) and lint checks (`make lint`) pass.
4. Open a Pull Request on GitHub describing the motivation and changes made.
