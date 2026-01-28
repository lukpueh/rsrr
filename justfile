# https://just.systems

default:
    just --list

lint:
    uvx ruff check && uvx ruff format --check

lint-fix:
    uvx ruff check --fix && uvx ruff format
