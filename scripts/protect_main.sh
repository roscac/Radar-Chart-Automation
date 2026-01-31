#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed." >&2
  exit 1
fi

if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo "Error: gh is not authenticated. Run 'gh auth login'." >&2
  exit 1
fi

remote_url=$(git remote get-url origin 2>/dev/null || true)
if [[ -z "${remote_url}" ]]; then
  echo "Error: Could not find git remote 'origin'." >&2
  exit 1
fi

owner=""
repo=""

if [[ "${remote_url}" =~ ^git@github.com:([^/]+)/(.+?)(\.git)?$ ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}"
elif [[ "${remote_url}" =~ ^https?://github.com/([^/]+)/(.+?)(\.git)?$ ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}"
else
  echo "Error: Unsupported remote URL format: ${remote_url}" >&2
  exit 1
fi

if [[ -z "${owner}" || -z "${repo}" ]]; then
  echo "Error: Failed to parse owner/repo from remote: ${remote_url}" >&2
  exit 1
fi

# TODO: Replace the placeholder with your actual CI check contexts.
# Example: ["CI / ci (ubuntu-latest)", "CI / ci (macos-latest)", "CI / ci (windows-latest)"]
read -r -d '' payload <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "REPLACE_ME_WITH_ACTUAL_STATUS_CHECK_NAME"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

set +e
response=$(gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${owner}/${repo}/branches/main/protection" \
  --input - <<<"${payload}" 2>&1)
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  echo "Failed to apply branch protection to ${owner}/${repo} (main)." >&2
  echo "Response:" >&2
  echo "${response}" >&2
  exit ${status}
fi

echo "Branch protection applied to ${owner}/${repo} (main)."
