#!/usr/bin/env bash
#
# org-commits.sh  –  GitHub organisation commit statistics for the past year
#
# For each repository in <org>, prints the number of commits made in the past
# 365 days, then lists every distinct GitHub username that authored at least
# one of those commits.
#
# Notes:
#   • Commits whose git author e-mail is not linked to a GitHub account are
#     omitted from the author list (their count is still included).
#   • Large organisations with many busy repos can trigger GitHub's secondary
#     rate limits; uncomment the sleep line in the loop if that happens.
#   • Archived repos are included by default (type=all).
#
# Prerequisites: gh CLI (authenticated), jq, bash ≥ 3.2
# Usage:         ./org-commits.sh <github-org>

set -euo pipefail

ORG="${1:?Usage: $0 <github-org>}"

# ── Portable "1 year ago" ISO-8601 timestamp ──────────────────────────────────
if date -v-1y >/dev/null 2>&1; then
    SINCE=$(date -u -v-1y +%Y-%m-%dT%H:%M:%SZ)   # macOS / BSD date
else
    SINCE=$(date -u -d '1 year ago' +%Y-%m-%dT%H:%M:%SZ)  # Linux / GNU date
fi

AUTHORS=$(mktemp)
trap 'rm -f "$AUTHORS"' EXIT

log() { printf '%s\n' "$*" >&2; }

log "Organisation : $ORG"
log "Since        : $SINCE"
log ""

# ── 1. Fetch all repositories ──────────────────────────────────────────────────
log "Fetching repository list…"

repos=()
while IFS= read -r r; do
    [[ -n "$r" ]] && repos+=("$r")
done < <(
    gh api --paginate "/orgs/$ORG/repos?type=all&per_page=100" --jq '.[].name'
)

log "Found ${#repos[@]} repositories."
log ""

# ── 2. Per-repo commit counts ──────────────────────────────────────────────────
printf "%-50s  %s\n" "Repository" "Commits (past year)"
printf "%-50s  %s\n" "$(printf '%050d' 0 | tr 0 -)" "$(printf '%019d' 0 | tr 0 -)"

total=0

for repo in "${repos[@]}"; do
    printf '  %-60s\r' "→ $repo" >&2

    # gh --paginate applies --jq to every page; results are printed line-by-line.
    # author.login is null for git identities not linked to a GitHub account;
    # "// empty" silently skips those entries.
    logins=$(
        gh api --paginate \
            "/repos/$ORG/$repo/commits?since=${SINCE}&per_page=100" \
            --jq '.[].author.login // empty' \
            2>/dev/null \
        || true
    )

    count=0
    if [[ -n "$logins" ]]; then
        count=$(printf '%s\n' "$logins" | grep -c .)
        printf '%s\n' "$logins" >> "$AUTHORS"
        total=$((total + count))
    fi

    printf "%-50s  %d\n" "$repo" "$count"

    # Uncomment to avoid secondary rate limits on large orgs:
    # sleep 0.5
done

printf '%80s\r' '' >&2   # erase the last progress line

# ── 3. Summary ─────────────────────────────────────────────────────────────────
echo ""
printf "Total commits across all repos: %d\n" "$total"
echo ""

if [[ -s "$AUTHORS" ]]; then
    distinct=$(sort -u "$AUTHORS" | wc -l | tr -d ' ')
    printf "Distinct GitHub commit authors (%d):\n" "$distinct"
    printf "%-30s  %s\n" "Author" "Commits (past year)"
    printf "%-30s  %s\n" "$(printf '%030d' 0 | tr 0 -)" "$(printf '%019d' 0 | tr 0 -)"
    sort "$AUTHORS" | uniq -c | sort -rn | awk '{ printf "%-30s  %d\n", $2, $1 }'
else
    printf "No commits found in the past year.\n"
fi
