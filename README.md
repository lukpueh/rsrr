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
rsrr run --ef-project-id technology.csi -- ef_committers

# List available checks
rsrr list

```

## Access tokens

Several checks require API tokens. Create them with the minimum scopes needed
by the checks in this tool:

- **GitHub** (classic personal access token) — needed for Dependabot alerts,
  security advisories, and private-vulnerability-reporting endpoints. Pass via
  `--gh-token` or `GH_TOKEN`:

  [Create token](https://github.com/settings/tokens/new?description=rsrr&scopes=repo,security_events)
  (scopes: `repo`, `security_events`)

- **GitLab** (eclipse.org instance) — needed to search the
  `security/vulnerability-reports` project. Pass via `--gl-token` or
  `GL_TOKEN`:

  [Create token](https://gitlab.eclipse.org/-/user_settings/personal_access_tokens?name=rsrr&scopes=read_api)
  (scope: `read_api`)


## Usage Example

```bash

rsrr --verbose run \
    --gh-token $(gh auth token) \
    --gl-token ${GL_TOKEN} \
    --ef-project-id technology.csi \  # Review "Common Security Infrastructure" project
    --gh-repo eclipse-csi/otterdog \  # ... and focus on "Otterdog" repo
    --gl-vuln-kw otterdog --gl-vuln-kw self-service \  # Exemplary keywords to search vulnerability-reports
    --ctx-data otterdog-rsr.json
```

## Adding a new Check

Create a new file in `src/rsrr/checks/` with a descriptive name, e.g.
`ultimate_answer.py`, and add a `Check` implementation, e.g.

```python
from ..base import BaseCheck

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
