#!/bin/sh

# auto check for pep8 so we don't check in bad code
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -e '\.py$')

if [ -n "$FILES" ]; then
    ruff check pyxform tests
    ruff format pyxform tests
fi
