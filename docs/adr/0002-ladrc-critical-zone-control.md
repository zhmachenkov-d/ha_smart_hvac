# LADRC on Critical Zone air temperature with OpenTherm water setpoint

The HVAC App splits multi-zone coordination from control: the Multi-Zone Coordinator selects the Critical Zone (largest positive Zone Error) and passes its air temperature and reference setpoint to an ADRC Controller running LADRC. The controller commands Set Water Temperature on the Plant via a Home Assistant number entity — not zone thermostat setpoints.

Outdoor temperature enters as additive Weather Feedforward (linear baseline) on top of the LADRC tracking term. When no Zone has Heating Demand (all zone errors ≤ 0), the App writes **0** to Set Water Temperature, bypasses LADRC output, and resets observer state. When the Critical Zone changes, the ESO re-initializes from the new zone's measured temperature so observer state is not carried across rooms.

This differs from Huang et al. (2018), who control a single AHU zone by adjusting coil water **flow**; here the actuator is OpenTherm **water temperature** for a shared boiler serving multiple Zones. Huang `b₀`/`ωo` **must not** be used on this plant. Example defaults are thermal-band starting points and **need house calibration**.

The production `α = 1 − exp(−ωo·dt)` gain map (`exp_map`) at `dt=60` **fails** (gains saturate; thermal-band runs diverge) and **must not** return. The ESO **must** use continuous-form advance (`β1 = 2ωo`, `β2 = ωo²` over the sample). After the plant write `command = clamp(u_ff + u_track)`, ESO known input **must** be post-clamp `(command − u_ff)`.
