"""Offline tests for the release train — config, workflow shape, matrix rows."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from semantic_release.commit_parser.conventional.options import (
    ConventionalCommitParserOptions,
)
from semantic_release.enums import LevelBump

ROOT = Path(__file__).resolve().parents[1]


def _workflow() -> str:
    return (ROOT / ".github" / "workflows" / "release.yaml").read_text(encoding="utf-8")


def _semantic_release_config() -> dict:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["semantic_release"]


# --- Matrix: Releasing merge -------------------------------------------------


def test_matrix_releasing_merge_config_and_version_invocation():
    """Releasing merge: write-back, v* tag, Release w/o assets via `version`."""
    sr = _semantic_release_config()
    text = _workflow()

    assert sr["tag_format"] == "v{version}"
    assert sr["version_toml"] == ["pyproject.toml:project.version"]
    assert sr["allow_zero_version"] is True
    assert "uv lock --upgrade-package" in sr["build_command"]
    assert "git add uv.lock" in sr["build_command"]
    assert "uv build" not in sr["build_command"]
    assert sr["publish"]["upload_to_vcs_release"] is False

    assert "push:" in text
    assert "branches: [main]" in text
    assert "uv run semantic-release" in text
    assert re.search(r"semantic-release\s+-v\s+version\b", text)
    assert "semantic-release" in text and " publish" not in text
    assert "upload-artifact" not in text
    assert "softprops/action-gh-release" not in text


# --- Matrix: Non-releasing merge ---------------------------------------------


def test_matrix_non_releasing_merge_psr_defaults_and_writeback_subject():
    """Non-releasing merge: docs/ci/chore skip bump; write-back is chore(release)."""
    sr = _semantic_release_config()
    assert sr["commit_message"].startswith("chore(release):")

    # Project does not override commit_parser_options → PSR conventional defaults apply.
    assert "commit_parser_options" not in sr
    opts = ConventionalCommitParserOptions()
    assert "feat" in opts.minor_tags
    assert "fix" in opts.patch_tags
    for tag in ("docs", "ci", "chore", "build", "style", "refactor", "test"):
        assert tag in opts.other_allowed_tags
    assert opts.default_bump_level == LevelBump.NO_RELEASE


# --- Matrix: PAT write-back re-trigger ---------------------------------------


def test_matrix_pat_writeback_retrigger_non_releasing_and_not_filtered():
    """PAT write-back re-trigger: chore(release); workflow does not skip bot pushes."""
    sr = _semantic_release_config()
    text = _workflow()

    assert sr["commit_message"].startswith("chore(release):")
    # Under PSR defaults, chore → no release (see non-releasing matrix test).
    opts = ConventionalCommitParserOptions()
    assert "chore" in opts.other_allowed_tags
    assert opts.default_bump_level == LevelBump.NO_RELEASE

    # No job-/step-level filter that would suppress the PAT-driven second push.
    assert "github.actor" not in text
    assert "github.event.pusher" not in text
    assert "paths-ignore" not in text
    assert "[bot]" not in text


# --- Matrix: Missing/invalid secret ------------------------------------------


def test_matrix_missing_secret_requires_pat_never_github_token():
    """Missing/invalid secret: checkout + GH_TOKEN use SEMANTIC_RELEASE_TOKEN only."""
    text = _workflow()

    assert text.count("secrets.SEMANTIC_RELEASE_TOKEN") >= 2
    assert "token: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}" in text
    assert "GH_TOKEN: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}" in text
    assert "GITHUB_TOKEN" not in text
    assert "secrets.GITHUB_TOKEN" not in text


# --- Matrix: Already released tip --------------------------------------------


def test_matrix_already_released_tip_version_command_is_noop_path():
    """Already released tip: `version` is the no-op path (no forced bump).

    Does not require local tags (shallow clones may lack them). PSR's `version`
    command exits 0 with no new release when the tip is already released; we
    lock that invocation and that the workflow never forces major/minor/patch.
    """
    text = _workflow()
    assert re.search(r"semantic-release\s+-v\s+version\b", text)
    assert " publish" not in text
    assert "--major" not in text
    assert "--minor" not in text
    assert "--patch" not in text


# --- Shared packaging / shape guards -----------------------------------------


def test_release_workflow_concurrency_and_tip_alignment():
    text = _workflow()
    assert "cancel-in-progress: false" in text
    assert "fetch-depth: 0" in text
    assert "git checkout -B ${{ github.ref_name }}" in text
    assert "git reset --hard ${{ github.sha }}" in text
    assert "astral-sh/setup-uv@v5" in text
    assert 'python-version: "3.12"' in text
    assert "workflow_dispatch:" in text


def test_python_semantic_release_pinned_in_dev_group():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = data["dependency-groups"]["dev"]
    assert any("python-semantic-release" in dep for dep in dev)
