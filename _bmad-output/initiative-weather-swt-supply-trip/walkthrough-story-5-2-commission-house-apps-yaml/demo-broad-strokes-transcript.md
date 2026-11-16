# Demo: Story 5.2 Broad strokes

Generated: 2026-11-16T23:02:00+02:00

## 1. House diff vs pre-5.2 (commission surface)

```diff
--- apps/apps.yaml.pre-5.2
+++ apps/apps.yaml
@@ -1,15 +1,21 @@
 # House AppDaemon commission (gitignored). Do not commit.
 # Weather-curve SWT: outdoor_temperature + weather_feedforward.
 # TRV soft-close: valve_closure_floor + commissioned Sonoff closure/accuracy.
+# Flame short-on trip: flame_on + ch_active (+ min/hold).
 # Backup before 1.3: apps/apps.yaml.pre-1.3
 # Backup before 4.2 TRV soft-close: apps/apps.yaml.pre-4.2
+# Backup before 5.2 flame short-on: apps/apps.yaml.pre-5.2
 hvac:
   module: ha_smart_hvac
   class: HvacApp
   outdoor_temperature: sensor.indoor_outdoor_meter_794a
   plant_management: switch.opentherm_bridge_ch_enabled
   plant_setpoint: number.opentherm_bridge_control_setpoint
-  boiler_water: sensor.opentherm_bridge_boiler_water_temperature_degc
+  # Flame short-on trip (min True duration; hold = whole seconds latched at SWT 0).
+  flame_on: binary_sensor.opentherm_bridge_flame_on
+  ch_active: binary_sensor.opentherm_bridge_ch_active
+  flame_on_min_s: 300
+  flame_trip_hold_s: 900
   setpoint_min: 50
   setpoint_max: 60
   control_interval: 300
```

## 2. Offline parse_config (live house args)

```
flame_on = binary_sensor.opentherm_bridge_flame_on
ch_active = binary_sensor.opentherm_bridge_ch_active
flame_on_min_s = 300.0
flame_trip_hold_s = 900

removed keys: ['boiler_water']
added keys: ['ch_active', 'flame_on', 'flame_on_min_s', 'flame_trip_hold_s']
shared value mismatches: []
```

## 3. Tracked surfaces unchanged

```
(empty = not edited this story)
```
