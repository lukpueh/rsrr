#!/bin/bash
ORG="eclipse-theia"
SINCE="2025-03-04T00:00:00Z"
CURSOR=""
HAS_NEXT=true

while [ "$HAS_NEXT" = "true" ]; do
  RESULT=$(gh api graphql -f query='
    query($org: String!, $since: GitTimestamp!, $cursor: String) {
      organization(login: $org) {
        repositories(first: 100, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            isArchived
            defaultBranchRef {
              target {
                ... on Commit {
                  history(since: $since) {
                    totalCount
                  }
                }
              }
            }
          }
        }
      }
    }' -f org="$ORG" -f since="$SINCE" -f cursor="$CURSOR")

  echo "$RESULT" | jq -r '
    .data.organization.repositories.nodes[] |
    select(.isArchived == false) |
    [.name, (.defaultBranchRef.target.history.totalCount // 0)] |
    @tsv'

  HAS_NEXT=$(echo "$RESULT" | jq -r '.data.organization.repositories.pageInfo.hasNextPage')
  CURSOR=$(echo "$RESULT" | jq -r '.data.organization.repositories.pageInfo.endCursor')
done