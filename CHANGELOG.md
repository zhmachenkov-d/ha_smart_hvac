# CHANGELOG

<!-- version list -->

## v1.0.0 (2026-10-17)

### Bug Fixes

- **hacs**: Rename package and repo to ha_smart_hvac
  ([`5b7e17b`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/5b7e17bdaaaff49ed9f88f7a75efae6bca3c3a15))

### Chores

- **bmad**: Add PR #43 walkthrough and clear deferred Q5
  ([`644fbec`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/644fbecd930dbf2bd6bf54505462ac776c6b04ad))

- **bmad**: Drop duplicate PR #43 review-log stub
  ([`093756f`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/093756f76e9701b447407364550872792be8f769))

- **bmad**: Drop empty ticket keys from Package C oneshot plans
  ([`7376c8e`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/7376c8e4c373d3f0ec674e30f76694c3ec0c6189))

- **bmad**: Note PR #41 walkthrough wrap-up in review log
  ([`f5ebb4b`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/f5ebb4b87454b4776874d59a5ca2a9a94f9c5c85))

### Documentation

- **adr**: Close Package C clear_steady and WARN framing
  ([`6a05fbe`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/6a05fbe5013dfdd8c9d456f701ed61e1d16d8db3))

### Testing

- **hvac**: Add Package C deferred stub locks
  ([`22482cb`](https://github.com/zhmachenkov-d/ha_smart_hvac/commit/22482cbb004fe728715370af06f5aabd0cbd2d22))

### Breaking Changes

- **hacs**: Apps.yaml must use module: ha_smart_hvac; copy apps.yaml.example from the repo root.
  GitHub repo is now ha_smart_hvac.


## v0.5.1 (2026-10-17)

### Bug Fixes

- **hvac**: Clear steady on latch and once-per-episode blow-up WARN
  ([`754b30d`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/754b30d0e409546fb74fee2092dfd0e9461d8089))

### Chores

- **bmad**: Add omega-c gate epic retrospective and party C decision
  ([`3435c63`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/3435c63d01cf0cd4c1d9a28b695e89fe680677af))

- **bmad**: Note PR #36 walkthrough wrap-up in review log
  ([`57b25bc`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/57b25bc448820ebb20146521b44e47b8615c895b))

- **bmad**: Note PR #39 walkthrough wrap-up in review log
  ([`02556c5`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/02556c5dcfe554e2420aabef4ea6f62f48ce860c))

- **bmad**: Walkthrough PR #39 and close omega-c gate
  ([`dcdc8b6`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/dcdc8b6425cba80bae049de44c66f7b3274a0560))

### Documentation

- **omega-c**: Document criterion A guards in ADR and calibration
  ([`59350ce`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/59350cedc184f4444cc220849538f4d3388ad6b9))

### Refactoring

- **hvac**: Close omega-c gate epic with naming and companion sync
  ([`15c23bb`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/15c23bb80043fd605de20262346dd3603a293feb))

### Testing

- **hvac**: Harden Package C locks from walkthrough review
  ([`132f984`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/132f984412824b89243361f326008d49b601ee53))


## v0.5.0 (2026-10-17)

### Chores

- **bmad**: Add PR #36 walkthrough and mark story 1.3 done
  ([`62f77ae`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/62f77ae94f343640499a3a3bc55ac9cf30a17dad))

### Features

- **hvac**: Skip redundant plant setpoint writes
  ([`7177934`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/717793406de2cb1c41d0e945151bb7ca77697529))


## v0.4.0 (2026-10-17)

### Bug Fixes

- **hvac**: Sticky latch only after successful plant write
  ([`2a6c208`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/2a6c20802b7fab0cbcbeaedab2df34ac82148a04))

### Chores

- **bmad**: Mark story 1.1 directional clamp done
  ([`210471a`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/210471a2fd37ae95b2a8b1d71aeb1525180ae893))

- **bmad**: Note PR #31 walkthrough wrap-up in review log
  ([`ed68464`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/ed6846475507cbc080e3213acdf45661c4b5b776))

### Features

- **hvac**: Latch ωc decay and skip adapt while soft-kill held
  ([`e332fef`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/e332fef20223bb3db0b0264e527f78960599ea37))


## v0.3.0 (2026-10-17)

### Chores

- **bmad**: Add gate-ωc-on-saturation initiative artifacts
  ([`cd3c16f`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/cd3c16fdb2d60fa2a8f9a472a0977546edefa40e))

- **hvac**: Harden inspect lock and capture PR #31 walkthrough
  ([`dc141b7`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/dc141b7d103c6869e3cc092567ec63a5515b12e1))

### Features

- **hvac**: Gate ωc apply/commit on directional clamp
  ([`2868763`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/2868763d0f7191f63d5bc28bc4807aa73b6b7f1d))


## v0.2.5 (2026-10-16)

### Bug Fixes

- **hvac**: Apply LADRC retro package A and trip-path hygiene
  ([`5121a06`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/5121a06ea7de2a2421a2e4731deaa6a749b906a8))

### Chores

- **bmad**: Close LADRC blow-up epic and initiative
  ([`28f8728`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/28f8728d299b908844b2462c8e4408096f806176))

- **bmad**: Record walkthrough for PR #28 and mark story 1.5 done
  ([`9feac76`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9feac76b14270b475087573f78f904eded7fa512))

### Refactoring

- **hvac**: Sweep LADRC cleanup and zone-change latch hygiene
  ([`9cb6eed`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9cb6eedf1ad6298370c27bfd2207bf79327ae827))

### Testing

- **hvac**: Close LADRC retro verification gaps (AI-7)
  ([`224e9db`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/224e9dbbfba439742eae1a5e1514e5e454f35d63))


## v0.2.4 (2026-10-16)

### Bug Fixes

- **hvac**: Add LADRC u_track blow-up guard in hvac_app
  ([`18e21d1`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/18e21d100e4884fda3f3c824198872e228caeb14))

### Chores

- **bmad**: Record story 1.4 party-mode decisions in memlog
  ([`6d392ce`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/6d392ce28bf479539e058e1e63bf6478d61cdcf2))

- **bmad**: Record walkthrough for 18e21d1 and mark story 1.4 done
  ([`c4ecbd5`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/c4ecbd51982755b97bdc62d4aba22e22b6f1001c))

### Documentation

- Add house calibration guide and link from README
  ([`c6e3431`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/c6e34310f7ad7d257292889a514048fd54973697))


## v0.2.3 (2026-10-16)

### Bug Fixes

- **ladrc**: Retune defaults, add u_track_max, amend ADR 0002
  ([`81e3378`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/81e337898acdded76f56f66ae099f756bb8a8242))

### Documentation

- Add PR #26 walkthrough and mark story 1.3 done
  ([`f87e80e`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/f87e80e439f3f18a0ff97d99194cfbd9adff36d9))


## v0.2.2 (2026-10-16)

### Bug Fixes

- **hvac**: Advance ESO with tracking-residue known input
  ([`a424b61`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/a424b617ada0bf07f3a9d14644e83a575b6110eb))

### Documentation

- Append PR #24 walkthrough log for commit+push
  ([`2734472`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/2734472a45591acce16080c8b8bb20b7a2274bda))

- Close PR #24 walkthrough blocks for wrap-up
  ([`99a8ed6`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/99a8ed63531ba868a40f9777c514c660e8778560))

- Mark story 1.1 continuous-form ESO done
  ([`82ca04e`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/82ca04eb2ec05a6d47e1f365437e48b6509245b6))

### Testing

- **hvac**: Strengthen tracking-residue known-input locks
  ([`e4567ab`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/e4567abf337efa94f7dc7a36923387e679f4a747))


## v0.2.1 (2026-10-16)

### Bug Fixes

- **ladrc**: Replace exp_map ESO with continuous-form advance
  ([`035013b`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/035013b37679354b7dcb220f9e81ce3021d5f496))

### Documentation

- Add LADRC blow-up fix initiative, spec, and epic tickets
  ([`f1f0245`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/f1f0245a593f309dcc46ae92c99eb852f75b7a49))

- Add PR #22 walkthrough for continuous-form ESO
  ([`9e47a76`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9e47a76fcdca12ec0442cd74213d4cdc24adf5dc))

- Close CC-gate open-PR migration deferred entry
  ([`2d33ed8`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/2d33ed891774a0b5358c96fedfb1e190c6477d95))

- Close PR #22 walkthrough blocks
  ([`3096d4d`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/3096d4d01cdc4bcaa2a88d704ab7ba309ef096a6))

- Close PSR release-train deferred after v0.2.0 verify
  ([`9fdcbb6`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9fdcbb641c476528e15b843e4900ff2c35d0b037))

- Log walkthrough commit for PR #22
  ([`9ab2b74`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9ab2b74541dd682faa8db762539a6e5731285dc4))

- Reframe LADRC blow-up around continuous-form ESO
  ([`49612de`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/49612def4cd14d325164e2506d49a35e33daeb23))

- Update party-mode memlog for continuous-form ESO plan
  ([`be48666`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/be48666b1d1c008bfbd458329173cce3ec082e63))

### Testing

- **ladrc**: Tighten one-step Δz1 AC and Euler comment
  ([`8c09bc2`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/8c09bc2f568757f15db34e3612d009283fcf0872))


## v0.2.0 (2026-10-03)

### Chores

- Add MIT license for HACS Validate
  ([`cba655f`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/cba655f20275e3a40e307f4e42125494ee59db55))

### Continuous Integration

- Add Conventional Commits PR title and commits gate
  ([`6a67302`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/6a673029b6a00c54150fc62aad86b9d304c68e4f))

- Add python-semantic-release train for HACS releases
  ([`a1a5e05`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/a1a5e05389d7a6d9b04297781e1a9e818a6aad13))

- Run workflows on pull_request only
  ([`9a6501e`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/9a6501eed9f77364456614eb6c670c930f0a2a64))

### Documentation

- Add forged idea for HACS release automation
  ([`a530ca1`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/a530ca16c91ca1e89d7acf6bd29dd5e2ea106ea8))

- Add walkthrough for Conventional Commits PR gate
  ([`deee8a2`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/deee8a22e2b33be03cd283711f1e2a890ee01f4e))

- Add walkthrough for HACS semantic-release train
  ([`aeaf6a0`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/aeaf6a060896806e920379cd655476dc5936fc92))

- Advance HACS release-train walkthrough past Broad strokes
  ([`dec1b11`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/dec1b114bc27ab8440a89d9912a3fcb5c82742c1))

- Advance HACS release-train walkthrough to matrix tests
  ([`5eb73d4`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/5eb73d4ee33099254b611fcd18a604d6e517e967))

- Advance HACS release-train walkthrough to workflow slice
  ([`03a6766`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/03a67667e94785ec3a5e6b8ab18fc946dc5ffba9))

- Close HACS release-train walkthrough wrap-up
  ([`da51cb6`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/da51cb6ed388f05d5fa3d662db70ee274f408d70))

- Close out HACS publish Phase B residuals
  ([`5d0c67d`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/5d0c67dbd376487d6b38d210bb9b1423dbc1d894))

- Record PR #15 merge in release-train walkthrough
  ([`1bb33c7`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/1bb33c7fde633835c244427227195fac1fda5bcc))

### Features

- **hacs**: Enable render_readme in hacs.json
  ([`71780fc`](https://github.com/zhmachenkov-d/ha-smart-hvac/commit/71780fc9ab1ba437fdf48cf6fc3b966107ee15df))


## v0.1.0 (2026-10-03)

- Initial Release
