#!/bin/bash
# Fetch PDM official docs and CI/CD workflow references
set -e

DEST=/home/devk/projects/llm-api-scope/tmp/repo/pdm/docs
mkdir -p "$DEST"

fetch_md() {
    local path="$1"
    local name="$2"
    gh api "repos/pdm-project/pdm/contents/$path" --jq '.content' \
        | tr -d '\n' | base64 -d > "$DEST/$name"
    echo "[+] $DEST/$name"
}

fetch_md "docs/usage/publish.md" "publish.md"
fetch_md "docs/dev/contributing.md" "contributing.md"
fetch_md ".github/workflows/ci.yml" "ci.yml"
fetch_md ".github/workflows/release.yml" "release.yml"

gh api repos/pdm-project/setup-pdm/contents/README.md \
    --jq '.content' | tr -d '\n' | base64 -d > "$DEST/setup-pdm-readme.md"
echo "[+] $DEST/setup-pdm-readme.md"

ls -la "$DEST"
