# Demo: Story 4.2 Broad strokes

Generated: 2026-11-15T20:35:00+02:00

## 1. House diff vs pre-4.2 (commission surface)

```diff
--- apps/apps.yaml.pre-4.2	2026-11-15 14:01:58.451561391 +0000
+++ apps/apps.yaml	2026-11-15 14:05:18.454416725 +0000
@@ -1,6 +1,7 @@
 # House AppDaemon commission (gitignored). Do not commit.
 # Weather-curve SWT: outdoor_temperature + weather_feedforward.
 # Backup before 1.3: apps/apps.yaml.pre-1.3
+# Backup before 4.2 TRV soft-close: apps/apps.yaml.pre-4.2
 hvac:
   module: ha_smart_hvac
   class: HvacApp
@@ -11,6 +12,7 @@
   setpoint_min: 50
   setpoint_max: 60
   control_interval: 300
+  valve_closure_floor: 80
   weather_feedforward:
     base: 30
     slope: 1.0
@@ -25,13 +27,19 @@
     temperature: sensor.livingroom_sonoff_snzb_02d_temperature
     weight: 1.5
     thermostats:
-    - climate.livingroom_sonoff_trvzb_thermostat
-    - climate.livingroom_sonoff_trvzb_thermostat_2
+    - climate: climate.livingroom_sonoff_trvzb_thermostat
+      valve_closure: number.livingroom_sonoff_trvzb_valve_closure_degree
+      accuracy: number.livingroom_sonoff_trvzb_temperature_control_accuracy
+    - climate: climate.livingroom_sonoff_trvzb_thermostat_2
+      valve_closure: number.livingroom_sonoff_trvzb_valve_closure_degree_2
+      accuracy: number.livingroom_sonoff_trvzb_temperature_control_accuracy_2
   - name: children_bedroom
     temperature: sensor.childroom_sonoff_snzb_02d_temperature
     weight: 1.3
     thermostats:
-    - climate.childroom_sonoff_trvzb_thermostat
+    - climate: climate.childroom_sonoff_trvzb_thermostat
+      valve_closure: number.childroom_sonoff_trvzb_valve_closure_degree
+      accuracy: number.childroom_sonoff_trvzb_temperature_control_accuracy
   - name: kitchen
     temperature: sensor.kitchen_sonoff_snzb_02d_temperature
     weight: 1.0
@@ -41,7 +49,9 @@
     temperature: sensor.bedroom_sonoff_snzb_02d_temperature
     weight: 1.2
     thermostats:
-    - climate.bedroom_sonoff_trvzb_thermostat
+    - climate: climate.bedroom_sonoff_trvzb_thermostat
+      valve_closure: number.bedroom_sonoff_trvzb_valve_closure_degree
+      accuracy: number.bedroom_sonoff_trvzb_temperature_control_accuracy
   - name: wc
     temperature: sensor.wc_sonoff_snzb_02d_temperature
     weight: 0.4
```

## 2. Offline parse_config (live house args)

```
valve_closure_floor = 80.0

Commissioned TRVs:
  [living_room] climate.livingroom_sonoff_trvzb_thermostat
       closure=number.livingroom_sonoff_trvzb_valve_closure_degree
       accuracy=number.livingroom_sonoff_trvzb_temperature_control_accuracy
  [living_room] climate.livingroom_sonoff_trvzb_thermostat_2
       closure=number.livingroom_sonoff_trvzb_valve_closure_degree_2
       accuracy=number.livingroom_sonoff_trvzb_temperature_control_accuracy_2
  [children_bedroom] climate.childroom_sonoff_trvzb_thermostat
       closure=number.childroom_sonoff_trvzb_valve_closure_degree
       accuracy=number.childroom_sonoff_trvzb_temperature_control_accuracy
  [bedroom] climate.bedroom_sonoff_trvzb_thermostat
       closure=number.bedroom_sonoff_trvzb_valve_closure_degree
       accuracy=number.bedroom_sonoff_trvzb_temperature_control_accuracy

Plain climates (no TRV law):
  [bathroom] climate.bathroom_generic_thermostat
  [kitchen] climate.kitchen_generic_thermostat
  [wc] climate.wc_generic_thermostat
```

## 3. Tracked surfaces unchanged

```
(empty = not edited this story)
```
