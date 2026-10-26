#!/usr/bin/env bash
set -euo pipefail
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
curl --fail --silent --show-error --location --retry 3   https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz   -o "$work/gitleaks.tar.gz"
printf '%s  %s\n' 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb "$work/gitleaks.tar.gz" | sha256sum --check --status
tar -xzf "$work/gitleaks.tar.gz" -C "$work" gitleaks
"$work/gitleaks" git . --redact=100 --no-banner
printf 'Tested source: %s\n' "$(git rev-parse HEAD)"
sha256sum security/BASELINE.md
