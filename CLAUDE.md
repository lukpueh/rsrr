# rsrr - Rapid Security Review Runner

CLI tool for running automated checks for Eclipse Foundation Rapid Security Reviews.

## Architecture

```
src/rsrr/
  base.py            # BaseCheck ABC + Context dataclass
  checks/
    ef_project.py    # Example: fetch EF project API data
    <check_name>.py  # One file per check, each exports Check(BaseCheck)
  cli.py             # Click CLI: `rsrr list` and `rsrr run`
  runner.py          # Discovers checks, runs them in dependency waves (asyncio)
tests/
  test_cli.py        # CLI integration tests (Click CliRunner, mocked checks)
  test_runner.py     # Runner unit tests (discover, run, dependencies)
```

**Check discovery**: `runner.py` auto-discovers every `.py` file in `checks/` (except `base.py` and `__init__.py`) that exports `class Check(BaseCheck)`. The module filename (without `.py`) becomes the `check_id`.

**Dependency resolution**: Checks with `depends_on = ["other_check_id"]` run after their dependencies complete. Independent checks run in parallel via `asyncio.gather`. Results are stored in `ctx.data[check_id]`.

## Adding a Check

Create `src/rsrr/checks/<check_name>.py`:

```python
from ..base import BaseCheck

class Check(BaseCheck):
    name = "Human-readable name"
    comment = "One-line description"
    depends_on = ["ef_project"]  # optional, list of check_id strings

    async def run(self) -> Any:
        # Access dependency results via self.ctx.data["ef_project"]
        # Access project ID via self.ctx.ef_project_id
        return result  # stored in ctx.data["<check_name>"]
```

## Key Patterns

- Use `httpx.AsyncClient` for all HTTP calls (project uses httpx)
- GitHub API calls should use `headers={"Accept": "application/vnd.github.v3+json"}`
- GitHub API auth: pass token via `Authorization: Bearer <token>` header (check env for GH_TOKEN)
- `ctx.ef_project_id_normalized` replaces `.` with `_` (for module naming)
- EF project API: `https://projects.eclipse.org/api/projects/{project_id}`
- EF project result is a list; `result[0]["github"]["org"]` gives the GitHub org name

## Commands

```bash
uv run rsrr list              # list all available checks
uv run rsrr run --ef-project-id technology.csi  # run all checks
uv run rsrr run --ef-project-id technology.csi ef_project gh_default_security_policy  # run specific checks

just lint        # ruff check + format check
just lint-fix    # ruff check --fix + format

uv run pytest tests/           # run all tests
uv run pytest tests/ -v        # run tests with verbose output
```

## Project Setup

- **Package manager**: `uv` (lockfile: `uv.lock`)
- **Linter/formatter**: `ruff` (via `uvx`)
- **Task runner**: `just` (see `justfile`)
- **Python**: 3.13+
- **Key deps**: `click`, `httpx`
- **Test deps** (dev): `pytest`, `pytest-asyncio`

## Testing

Tests cover `cli.py` and `runner.py` — not individual check implementations.

- **CLI tests** (`tests/test_cli.py`): use `click.testing.CliRunner` with `unittest.mock.patch` on `get_all_checks` to inject fake check classes. No network calls.
- **Runner tests** (`tests/test_runner.py`): use simple `BaseCheck` subclasses defined inline. `test_discover_checks` writes temp modules to `tmp_path` and runs real discovery.
- Async tests use `@pytest.mark.asyncio` (requires `pytest-asyncio`; asyncio mode configured as `strict` in `pyproject.toml`).

## Directory Notes

- `research/` — shell scripts for exploring APIs (not part of the package)
- `.venv/` — managed by uv, do not edit manually
