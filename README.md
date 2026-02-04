# Rapid Security Review Runner

An extensible CLI to run automated checks for Eclipse Foundation Rapid Security
Reviews.

## Installation

```bash
uv tool install git+https://github.com/eclipse-csi/rsrr
```

## Usage

Check results are printed as JSON to stdout.

```bash
# Run all checks
rsrr run [opts]

# Run specific checks
rsrr run --ef-project-id technology.csi -- ef_committers_count

# List available checks
rsrr list

```

## Adding a new Check

Create a new file in `src/rsrr/checks/` with a descriptive name, e.g.
`ultimate_answer.py`, and add a `Check` implementation, e.g.

```python
from .base import BaseCheck

class Check(BaseCheck):
    name = "Ultimate Answer"
    comment = "Get the answer to the Ultimate Question of Life"

    async def run(self) -> int:
        return 42
```

Browse existing [`checks/`](src/rsrr/checks) for real-world examples.

## Development

This project uses [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
for project management, and
[`just`](https://github.com/casey/just?tab=readme-ov-file#installation)
to run commands. Look up their docs for installation and usage instructions.


```
# List available commands (recipes)
just -l
```
