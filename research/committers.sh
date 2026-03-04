#!/usr/bin/env bash
#
# Get list or committers (user IDs) for given Eclipse project (by project ID) .
# https://webdev.eclipse.org/docs/api/eclipse-projects-api/#tag/Projects/operation/RetrieveAProject
#
# HINT: Use PMI to get project IDs: https://projects.eclipse.org.
# The project ID is the last part of the URL of a project page. Dots ('.') in
# the name must be replaced with underscores ('_').
#
# Usage Example:
#
#       # https://projects.eclipse.org/projects/ecd.theia
#       ./get_committers.sh ecd_theia
#
set -euo pipefail

project_id=$1
committers=$(curl -s "https://projects.eclipse.org/api/projects/${project_id}" | \
   jq -r '.[0].committers.[].username')

for committer in $committers
do
   gh_user=$(curl -s "https://api.eclipse.org/account/profile/${committer}" | \
      jq -r '.github_handle')

   echo $committer $gh_user
done

