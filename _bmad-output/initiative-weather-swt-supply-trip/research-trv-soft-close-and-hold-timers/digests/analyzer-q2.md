# Analyzer Q2 @ 2ec1908

Thermostat string = climate only. Mapping requires climate+valve_closure+accuracy or ConfigError (config.py:135-137). commissioned property = both TRV fields non-None (models.py:17-18).

Listeners: _register_control_listeners from initialize after parse (hvac_app.py:47,60-75); if accuracy is not None → listen_state(control_event, accuracy). No listen on valve_closure. control_event → _apply_trv_law then prelude.

apps.yaml.example shows paired mapping + climate-only string.

Not found: listen on valve_closure; use of .commissioned property in hvac_app (uses None checks).
