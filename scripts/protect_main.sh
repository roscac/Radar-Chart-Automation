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

# Resolve CI status check contexts from the latest CI workflow run.
# Fallback to the placeholder if we cannot detect them.
contexts_json='["REPLACE_ME_WITH_ACTUAL_STATUS_CHECK_NAME"]'

workflow_id=$(gh api "/repos/${owner}/${repo}/actions/workflows/ci.yml" --jq .id 2>/dev/null || true)
if [[ -n "${workflow_id}" ]]; then
  run_id=$(gh api "/repos/${owner}/${repo}/actions/workflows/${workflow_id}/runs?branch=${branch}&per_page=1" --jq '.workflow_runs[0].id' 2>/dev/null || true)
  if [[ -n "${run_id}" ]]; then
    workflow_name=$(gh api "/repos/${owner}/${repo}/actions/runs/${run_id}" --jq .name 2>/dev/null || true)
    if [[ -n "${workflow_name}" ]]; then
      job_names=$(gh api "/repos/${owner}/${repo}/actions/runs/${run_id}/jobs?per_page=100" --jq '.jobs[].name' 2>/dev/null || true)
      if [[ -n "${job_names}" ]]; then
        contexts_json=$(printf '%s\n' "${job_names}" | awk -v wf="${workflow_name}" 'NF{print "\"" wf " / " $0 "\""}' | paste -sd, - | sed 's/^/[/' | sed 's/$/]/')
      fi
    fi
  fi
fi

payload=$(cat <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ${contexts_json}
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
)

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
