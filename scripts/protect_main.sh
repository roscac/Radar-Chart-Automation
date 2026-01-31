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

clean_url="${remote_url%.git}"
clean_url="${clean_url%/}"

if [[ "${clean_url}" == git@github.com:* ]]; then
  path="${clean_url#git@github.com:}"
  owner="${path%%/*}"
  repo="${path#*/}"
elif [[ "${clean_url}" == https://github.com/* ]] || [[ "${clean_url}" == http://github.com/* ]]; then
  path="${clean_url#https://github.com/}"
  path="${path#http://github.com/}"
  owner="${path%%/*}"
  repo="${path#*/}"
else
  echo "Error: Unsupported remote URL format: ${remote_url}" >&2
  exit 1
fi

if [[ -z "${owner}" || -z "${repo}" ]]; then
  echo "Error: Failed to parse owner/repo from remote: ${remote_url}" >&2
  exit 1
fi

# Detect default branch from GitHub; fallback to main if not found.
default_branch=$(gh api "/repos/${owner}/${repo}" --jq .default_branch 2>/dev/null || true)
branch="${default_branch:-main}"

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
  "/repos/${owner}/${repo}/branches/${branch}/protection" \
  --input - <<<"${payload}" 2>&1)
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  echo "Failed to apply branch protection to ${owner}/${repo} (${branch})." >&2
  echo "Response:" >&2
  echo "${response}" >&2
  exit ${status}
fi

echo "Branch protection applied to ${owner}/${repo} (${branch})."
