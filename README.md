# ha_smart_hvac

[![CI](https://github.com/zhmachenkov-d/ha_smart_hvac/actions/workflows/ci.yaml/badge.svg)](https://github.com/zhmachenkov-d/ha_smart_hvac/actions/workflows/ci.yaml)

AppDaemon apps for multi-zone OpenTherm HVAC control via Home Assistant.

## Install with HACS (custom repository)

This project ships as a **HACS AppDaemon** app (custom repository only — not in the HACS default store).

1. In Home Assistant, open **HACS** → enable AppDaemon discovery if needed → **Custom repositories**.
2. Add this repository URL, category **AppDaemon**, and install **ha_smart_hvac**.
3. Install from a **published GitHub Release** (HACS prefers releases over the default branch alone). After `v0.1.0`, Releases are cut automatically by CI when releasing changes merge to `main`.
4. HACS downloads the package to the HA config tree under `appdaemon/apps/ha_smart_hvac/` (e.g. `/config/appdaemon/apps/ha_smart_hvac/` on many HAOS installs). If your AppDaemon add-on’s default apps directory is elsewhere (common after add-on v0.15+ under `addon_configs/…`), point `app_dir` at the **parent** of that folder so AppDaemon can import the package ([hacs/integration#4442](https://github.com/hacs/integration/issues/4442)):

   ```yaml
   appdaemon:
     # HAOS / Supervised typical HA config mount; adjust if your install differs
     app_dir: /config/appdaemon/apps
   ```

5. Create `apps.yaml` **beside** the downloaded `ha_smart_hvac/` under that `app_dir` (HACS only installs the package directory under `apps/`; the wiring example is **not** in the download). Copy the example from the GitHub repo and replace `YOUR_*` placeholders with your entity IDs (never commit live house IDs):

   [apps.yaml.example](https://raw.githubusercontent.com/zhmachenkov-d/ha_smart_hvac/main/apps.yaml.example)

   Use `module: ha_smart_hvac` and `class: HvacApp` as in the example. After wiring, calibrate feedforward and rise-rate auto-correct for the house: [docs/house-calibration.md](docs/house-calibration.md).

## Layout

| Path | Role |
|------|------|
| `apps/ha_smart_hvac/` | HVAC App package (`module: ha_smart_hvac`, `class: HvacApp`) — sole directory under `apps/` (HACS requirement) |
| `apps/apps.yaml` | Local house entity wiring (**gitignored** — copy from example) |
| `apps.yaml.example` | Placeholder entity IDs only (repo root — not under `apps/`) |
| `appdaemon/` | Exclusive Session AppDaemon config (`appdaemon.yaml`, secrets) |
| `docs/house-calibration.md` | How to calibrate wiring, feedforward, and rise-rate auto-correct for a house |

Canonical Python lives at repo-root `apps/ha_smart_hvac/`. Exclusive Session config stays under `appdaemon/` and loads that tree via `app_dir: ../apps` (no symlink).

## Dev Container (Exclusive Session)

1. Copy env and fill HA credentials (plus optional `GH_TOKEN` on the **host** for `gh`):

   ```bash
   cp .env.example .env
   ```

2. Open the folder in a Dev Container (**Dev Containers: Reopen in Container**).
   Python 3.12 and dependencies install via `uv sync --group dev` in `postCreateCommand`.

3. Ensure local wiring exists:

   ```bash
   cp apps.yaml.example apps/apps.yaml
   # then replace YOUR_* placeholders with your house entity IDs
   ```

4. **Exclusive Session:** stop or disable the Production AppDaemon add-on in Home Assistant.

5. Start AppDaemon:

   ```bash
   ./scripts/run-appdaemon
   ```

   The script regenerates `appdaemon/secrets.yaml` from `.env`, then runs
   `appdaemon -c appdaemon/`. With `app_dir: ../apps` in `appdaemon/appdaemon.yaml`,
   AppDaemon loads the package from repo-root `apps/` (no symlink under `appdaemon/apps`).

6. When finished: stop AppDaemon (Ctrl+C), then start the Production Add-on again.

`HA_URL` must be a LAN address reachable from inside the container (not
`localhost` unless HA shares that network namespace).

Location fields in `appdaemon/appdaemon.yaml` are placeholders (`UTC` / `0,0`);
set them before relying on time or sun helpers.

## `app_dir` examples

AppDaemon resolves a relative `app_dir` against its config directory. Absolute paths are common on HAOS.

### 1. Exclusive Session (this repo)

In `appdaemon/appdaemon.yaml`, with `./scripts/run-appdaemon` → `appdaemon -c appdaemon/`:

```yaml
appdaemon:
  app_dir: ../apps
```

That resolves to `<repo>/apps`, where `ha_smart_hvac/` and your local `apps.yaml` live.

### 2. Production AppDaemon add-on (this house)

Per the [AppDaemon add-on Paths](https://appdaemon.readthedocs.io/en/latest/ADDON.html#paths) table, add-on config is `/config` inside the container (Samba/host: `addon_configs/a0d7b954_appdaemon`). AppDaemon’s default apps directory is `./apps` under that config — i.e. `/config/apps` in the container. You can omit `app_dir` or set it explicitly; keep house wiring on the HA host only (not in this git tree).

```yaml
appdaemon:
  # Explicit form of the add-on default (./apps under /config)
  app_dir: /config/apps
```

### 3. Stranger HACS install

Same path as the Install section above: when the add-on default differs from the HACS download location, set:

```yaml
appdaemon:
  # HAOS / Supervised typical HA config mount; adjust if your install differs
  app_dir: /config/appdaemon/apps
```

## Quality checks

```bash
uv sync --group dev        # install runtime + dev deps
uv run pytest              # run tests
uv run ruff check apps tests
uv run ruff format --check apps tests
pre-commit install         # optional: run hooks on commit
```
