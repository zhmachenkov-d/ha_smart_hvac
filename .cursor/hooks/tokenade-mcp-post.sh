#!/usr/bin/env bash
# Project-level Cursor postToolUse entrypoint for Tokenade MCP folding.
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
  exec "${bin}" hookwrap-cursor-mcp-post "$@"
fi

# Fail open: never block the agent if Tokenade is missing.
exit 0
