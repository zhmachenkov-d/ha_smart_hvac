# ha_smart_hvac
[[image: CI]](https://github.com/zhmachenkov-d/ha_smart_hvac/actions/workflows/ci.yaml)

AppDaemon apps for multi-zone OpenTherm HVAC control via Home Assistant.

## Install (AppDaemon)
1. Place the `ha_smart_hvac/` package under your AppDaemon apps directory (copy `apps/ha_smart_hvac/` from inside a [published GitHub Release](https://github.com/zhmachenkov-d/ha_smart_hvac/releases) source tarball, or from this repo’s `apps/ha_smart_hvac/`). After `v0.1.0`, Releases are cut automatically by CI when releasing changes merge to `main`.
2. Create `apps.yaml` **beside** that package under the same `app_dir`. Copy the example from the GitHub repo and replace `YOUR_*` placeholders with your entity IDs (never commit live house IDs):

   [apps.yaml.example](https://raw.githubusercontent.com/zhmachenkov-d/ha_smart_hvac/main/apps.yaml.example)

   Use `module: ha_smart_hvac` and `class: HvacApp` as in the example. After wiring, commission Outdoor Temperature and Weather Feedforward for the house: [docs/house-calibration.md](docs/house-calibration.md).

3. Point AppDaemon `app_dir` at the parent of `ha_smart_hvac/` if it is not already the add-on default (see [`app_dir` examples](#app_dir-examples)).

## Layout
| Path | Role |
| --- | --- |
| `apps/ha_smart_hvac/` | HVAC App package (`module: ha_smart_hvac`, `class: HvacApp`) — sole tracked directory under `apps/` |
| `apps/apps.yaml` | Local house entity wiring (**gitignored** — copy from example) |
| `apps.yaml.example` | Placeholder entity IDs plus Outdoor+FF commission template (`weather_feedforward` + example rails; repo root — not under `apps/`) |
| `appdaemon/` | Exclusive Session AppDaemon config (`appdaemon.yaml`, secrets) |
| `docs/house-calibration.md` | How to calibrate wiring, Outdoor Temperature, and Weather Feedforward for a house |

Canonical Python lives at repo-root `apps/ha_smart_hvac/`. Exclusive Session config stays under `appdaemon/` and loads that tree via `app_dir: ../apps` (no symlink).

## Dev Container (Exclusive Session)
1. Copy env and fill HA credentials (plus optional `GH_TOKEN` on the **host** for `gh`):

```sh
   cp .env.example .env
   ```
2. Open the folder in a Dev Container (**Dev Containers: Reopen in Container**).
   Python 3.12 and dependencies install via `uv sync --group dev` in `postCreateCommand`; Tokenade (`@tokenade/cli`) is installed and wired for Cursor there as well.

3. Ensure local wiring exists:

```sh
   cp apps.yaml.example apps/apps.yaml
   # then replace YOUR_* placeholders with your house entity IDs
   ```
4. **Exclusive Session:** stop or disable the Production AppDaemon add-on in Home Assistant.

5. Start AppDaemon:

```sh
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

```yml
appdaemon:
  app_dir: ../apps
```
That resolves to `<repo>/apps`, where `ha_smart_hvac/` and your local `apps.yaml` live.

### 2. Production AppDaemon add-on (this house)
Per the [AppDaemon add-on Paths](https://appdaemon.readthedocs.io/en/latest/ADDON.html#paths) table, add-on config is `/config` inside the container (Samba/host: `addon_configs/a0d7b954_appdaemon`). AppDaemon’s default apps directory is `./apps` under that config — i.e. `/config/apps` in the container. You can omit `app_dir` or set it explicitly; keep house wiring on the HA host only (not in this git tree).

```yml
appdaemon:
  # Explicit form of the add-on default (./apps under /config)
  app_dir: /config/apps
```
## Quality checks
```sh
uv sync --group dev        # install runtime + dev deps
uv run pytest              # run tests
uv run ruff check apps tests
uv run ruff format --check apps tests
pre-commit install         # optional: run hooks on commit
```