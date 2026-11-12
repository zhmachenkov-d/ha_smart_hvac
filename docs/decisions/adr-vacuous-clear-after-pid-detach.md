# Vacuous clear after PID detach

Once fixed PID ∫ / `y_prev` and RLS overlay leave the live App, plant-off and idle keep their write / no-write semantics only — there is no `_clear_pid_ephemeral` helper and no water-path ephemeral to clear until epic 2 trip state exists. Recorded from story 1.2 plan F1-A (`story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md`) and commits `a5f49190` / `d5e0a0f4`, because epic R2/R3 still say “clear ephemeral / water-path state” and the vacuous reading is surprising without this note.
