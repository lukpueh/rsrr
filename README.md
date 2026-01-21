# Rapid Security Review Runner

A CLI tool to run automated checks for Eclipse Foundation Rapid Security Reviews.


## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run all checks
rsrr run

# Run specific checks
rsrr run api_health random_number

# List available checks
rsrr list

# Output as JSON
rsrr run --format json
```

## Adding a New Check

Create a new file in `rsrr/checks/`, e.g., `my_check.py`:

```python
import asyncio
import urllib.request

from .base import BaseCheck


class Check(BaseCheck):
    name = "My Check"
    comment = "Description of what this check does"

    async def run(self) -> int:  # Return int, float, bool, or str
        loop = asyncio.get_event_loop()
        req = urllib.request.Request("https://api.example.com/endpoint")
        resp = await loop.run_in_executor(
            None, lambda: urllib.request.urlopen(req, timeout=10)
        )
        # Parse response and return scalar value
        return 42
```

Or with `httpx` for cleaner async HTTP (add to dependencies):

```python
import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "My Check"
    comment = "Description of what this check does"

    async def run(self) -> int:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.example.com/endpoint")
            return resp.json()["value"]
```

The check is automatically discovered and available as `my_check` (derived from the filename).

## Output Formats

### Plain (default)

```
✓ API Health [api_health]: True
  # Returns true if httpbin responds with 200
✓ Random Number [random_number]: 42
  # Fetches a random integer from random.org
```

### JSON

```json
[
  {
    "id": "api_health",
    "name": "API Health",
    "comment": "Returns true if httpbin responds with 200",
    "value": true,
    "success": true,
    "error": null
  }
]
```

## Exit Codes

- `0` - All checks passed
- `1` - One or more checks failed