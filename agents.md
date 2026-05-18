# AI Agent Development Restrictions

This document summarizes the standards and restrictions enforced during the development of this collection to ensure professional-grade code quality and Ansible Galaxy compliance.

## Code Quality & Standards
- **Strict Typing**: All Python code in `plugins/` must use type hints (via `typing` module) for all function arguments and return types.
- **Linting Compliance**: Code must pass `ruff` and `ansible-lint` checks with zero errors.
- **Modern Python**: Use built-in types (e.g., `dict`, `list`) where possible and `Optional`, `Union`, etc. for complex types.
- **No Placeholders**: Functional demonstrations must use real-world logic or generated images/data, never generic placeholders.

## Testing Standards
- **Mock-Driven Unit Tests**: All modules must have corresponding unit tests in `tests/unit/` using `pytest` and `unittest.mock`.
- **API Parity**: Mock responses must accurately reflect the structure and behavior of the UniFi API (both v2 Policy API and REST API).
- **Assertion Strictness**: Tests must verify both positive (successful execution) and negative (failure handling) paths.

## Packaging & Distribution
- **Minimal Artifacts**: The built collection (`.tar.gz`) must only contain files necessary for execution and documentation.
- **Excluded Files**: Development-only files (Makefiles, CI configs, test suites, virtual environments, AI metadata) are explicitly excluded from the build.
- **Standardized Build Path**: Release artifacts are consolidated into the `releases/` directory.

## Licensing Policy
- **Collection License**: This repository uses the MIT license (see `LICENSE.md` and `galaxy.yml`).
- **Module Header Standard**: Python modules in `plugins/modules/` must use `# MIT License (see LICENSE.md)` in their file headers.
- **No GPL Header Text**: Do not introduce GNU GPL header text in this collection unless the project license model is explicitly changed.

## Project Vision
- **Professional Grade**: The collection aims to be "Professional Grade" for public release on Ansible Galaxy, emphasizing reliability, documentation, and ease of use.
