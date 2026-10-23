#!/usr/bin/env bash
# Copy prd-development and user-story into the Cursor user skills folder.
# Those two skills come from deanpeters/Product-Manager-Skills (CC BY-NC-SA 4.0).
# This script does not vendor them into this repository.
set -euo pipefail

dest="${HOME}/.cursor/skills"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone --depth 1 https://github.com/deanpeters/Product-Manager-Skills "$tmp/pm-skills"
mkdir -p "$dest"
rm -rf "$dest/prd-development" "$dest/user-story"
cp -R "$tmp/pm-skills/skills/prd-development" "$tmp/pm-skills/skills/user-story" "$dest/"

echo "Installed prd-development and user-story into ${dest}"
