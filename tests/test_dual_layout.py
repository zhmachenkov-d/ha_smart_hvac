"""Dual-layout packaging invariants."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILTERED_APPS_YAML_PATHS = (
    "appdaemon/apps/apps.yaml",
    "apps/apps.yaml",
)


def test_exclusive_session_app_dir_points_at_repo_apps():
    text = (ROOT / "appdaemon" / "appdaemon.yaml").read_text(encoding="utf-8")
    assert "app_dir: ../apps" in text
    assert not (ROOT / "appdaemon" / "apps" / "ha_smart_hvac").exists()
    assert not (ROOT / "appdaemon" / "apps").is_symlink()


def test_apps_contains_only_package_directory():
    """Tracked apps/ holds only the package directory; no sibling files."""
    apps = ROOT / "apps"
    tracked = subprocess.check_output(
        ["git", "ls-files", "apps"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert tracked, "expected tracked files under apps/"
    for path in tracked:
        assert path.startswith("apps/ha_smart_hvac/"), path
    assert (apps / "ha_smart_hvac" / "__init__.py").is_file()
    assert not (apps / "apps.yaml.example").exists()


def test_fresh_clone_example_has_placeholders_only():
    example = ROOT / "apps.yaml.example"
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    assert "YOUR_" in text
    assert "module: ha_smart_hvac" in text
    tracked = subprocess.check_output(
        ["git", "ls-files", "apps.yaml.example", "apps"],
        cwd=ROOT,
        text=True,
    )
    assert "apps.yaml.example" in tracked
    assert "apps/apps.yaml\n" not in tracked and not tracked.endswith("apps/apps.yaml")


def test_history_has_no_live_apps_yaml_entity_ids():
    out = subprocess.check_output(
        [
            "git",
            "log",
            "--all",
            "--",
            *FILTERED_APPS_YAML_PATHS,
        ],
        cwd=ROOT,
        text=True,
    )
    assert out.strip() == "", "filtered apps.yaml paths still present in history"


def test_readme_production_app_dir_example():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "addon_configs/a0d7b954_appdaemon" in readme
    assert "app_dir: /config/apps" in readme
    assert "appdaemon.readthedocs.io" in readme
    assert "app_dir: /config/appdaemon/apps" not in readme
    assert "hacs" not in readme.lower()


def test_readme_install_first_before_exclusive_session():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    install_markers = (
        "## Install (AppDaemon)",
        "published GitHub Release",
        "apps.yaml.example",
    )
    for marker in install_markers:
        assert marker in readme
    install_idx = min(readme.index(m) for m in install_markers)
    exclusive_idx = readme.index("Exclusive Session")
    run_script_idx = readme.index("./scripts/run-appdaemon")
    assert install_idx < exclusive_idx
    assert install_idx < run_script_idx


def test_hacs_surface_removed():
    assert not (ROOT / "hacs.json").exists()
    assert not (ROOT / ".github" / "workflows" / "validate.yaml").exists()
    workflows = ROOT / ".github" / "workflows"
    for path in sorted(workflows.glob("*.yaml")) + sorted(workflows.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        assert "hacs/action" not in text, path
        assert "category: appdaemon" not in text, path
