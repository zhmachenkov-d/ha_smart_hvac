#!/usr/bin/env bash
# Project-level Cursor preToolUse entrypoint for Tokenade (cloud agents load
# only .cursor/hooks.json; resolve the binary without baking in an nvm path).
set -euo pipefail

resolve_tokenade() {
  if command -v tokenade >/dev/null 2>&1; then
    command -v tokenade
    return 0
  fi
  local candidate
  for candidate in \
    "${NVM_DIR:-/usr/local/share/nvm}/current/bin/tokenade" \
    "${HOME}/.nvm/current/bin/tokenade" \
    /usr/local/bin/tokenade
  do
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

if bin="$(resolve_tokenade)"; then
  exec "${bin}" hookwrap-pretool "$@"
fi

# Fail open: never block the agent if Tokenade is missing.
printf '%s\n' '{"permission":"allow"}'
exit 0
