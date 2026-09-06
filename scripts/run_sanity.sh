#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="hellqvio86"
COLLECTION="unifi"

# If already inside an ansible_collections hierarchy without symlink indirection:
REAL_PATH="$(pwd -P)"
if [[ "$REAL_PATH" =~ .*/ansible_collections/[^/]+/[^/]+$ ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/ansible-test" ]]; then
        exec "$REPO_ROOT/.venv/bin/ansible-test" sanity --local "$@"
    else
        exec ansible-test sanity --local "$@"
    fi
fi

SANDBOX_DIR="$(mktemp -d -t ansible_test_sanity_XXXXXX)"
cleanup() {
    rm -rf "$SANDBOX_DIR"
}
trap cleanup EXIT

TARGET_DIR="$SANDBOX_DIR/ansible_collections/$NAMESPACE/$COLLECTION"
mkdir -p "$TARGET_DIR"

rsync -a \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='.ansible' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='releases' \
    --exclude='debug' \
    --exclude='ansible_collections' \
    "$REPO_ROOT/" "$TARGET_DIR/"

cd "$TARGET_DIR"

if [[ -x "$REPO_ROOT/.venv/bin/ansible-test" ]]; then
    ANSIBLE_TEST="$REPO_ROOT/.venv/bin/ansible-test"
else
    ANSIBLE_TEST="ansible-test"
fi

# Conditionally skip legacy Python 2 boilerplate tests on older ansible-core (e.g. 2.16)
SKIP_ARGS=()
HELP_TEXT="$("$ANSIBLE_TEST" sanity --help 2>&1 || true)"
if echo "$HELP_TEXT" | grep -q "future-import-boilerplate"; then
    SKIP_ARGS+=(--skip-test future-import-boilerplate)
fi
if echo "$HELP_TEXT" | grep -q "metaclass-boilerplate"; then
    SKIP_ARGS+=(--skip-test metaclass-boilerplate)
fi

"$ANSIBLE_TEST" sanity --local ${SKIP_ARGS[@]+"${SKIP_ARGS[@]}"} "$@"
