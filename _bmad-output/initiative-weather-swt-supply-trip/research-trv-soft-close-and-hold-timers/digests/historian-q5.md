# Historian Q5 @ 2ec1908

Load-bearing: 784fc71 "feat(trv): add idle max-close soft-close for Sonoff valves" #146 — introduced pair-mandatory valve_closure+accuracy, ThermostatConfig.commissioned, overshoot law using accuracy band.

Follow-ons: b4d7603 latched without unread accuracy #146; e1a3c81 listen accuracy on control_event #148; eb79e95 abs(accuracy) #161; ef4d7a0 inclusive >= threshold #162.

2ec1908 is merge #163 replan; does not invent the accuracy requirement.

One-line: commissioned requires accuracy because story 4.1 defined Sonoff wiring as closure+accuracy for overshoot hysteresis, later made band robust and reactive — not because a later replan added the field.
