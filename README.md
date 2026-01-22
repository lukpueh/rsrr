# Rapid Security Review Runner

A CLI tool to run automated checks for Eclipse Foundation Rapid Security Reviews.


## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run all checks
rsrr run [opts]

# Run specific checks
rsrr run --gh-org eclipse-csi -- gh_org gh_dotgithub

# List available checks
rsrr list

```

## Adding a New Check

Create a new file in `rsrr/checks/`, e.g., `check_answer.py` and add a `Check`
implementation, e.g.:

```python

from .base import BaseCheck, ScalarResult

class Check(BaseCheck):
    name = "Check Answer"
    comment = "Get the answer to the Ultimate Question of Life"

    async def run(self) -> ScalarResult:
        return 42
```

The check is automatically discovered and available as `check_answer` (derived from the filename).

## Example output

```
rsrr run --gh-org eclipse-csi

✓ GitHub .github Repo [gh_dotgithub]: True
  # Checks if the organization has a .github repository
✓ GitHub Organization [gh_org]: True
  # Checks if the GitHub organization is indeed an organization
```

## Exit Codes

- `0` - All checks passed
- `1` - One or more checks failed