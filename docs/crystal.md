# Crystal Layer

This page documents the crystal-side workflow and the crystal -> OPO handoff.

## Role

The crystal layer consumes the cavity export and defines the nonlinear operating point used downstream.

The entry point is:

- `src/crystal/crystal_main.py`

## What `crystal_main.py` Does

The crystal script:

- loads the cavity JSON
- resolves the crystal material and interaction type
- computes the phase-matching scan
- computes the phase-matching resonance diagnostic
- optionally computes the double-resonance scan
- builds candidate operating points
- selects one active operating point
- evaluates active crystal quantities at that point
- exports the crystal JSON and plots

## Operating-Point Logic

The current operating-point selector is:

- `OPERATING_POINT_MODE`

Supported modes:

- `phase_matching`
- `double_resonance`

The selected candidate is exported as:

- `results.selected_operating_point_mode`
- `results.selected_operating_point`

## `active_for_opo`

The main OPO-facing crystal block is:

- `results.active_for_opo`

It contains the resolved active crystal state:

- operating-point mode
- active temperature
- active crystal length
- active phase-matching summary
- active mode matching
- active Boyd-Kleinman summary
- active polarization-resonance diagnostic

This is the intended single source of truth for OPO.

## Crystal Outputs Intended For OPO

The OPO layer primarily needs:

- `active_for_opo.phase_matching`
- `active_for_opo.mode_matching`
- `active_for_opo.boyd_kleinman_analysis`
- `active_for_opo.polarization_resonance`
- `active_for_opo.temperature_K`
- `active_for_opo.crystal_length_m`

The crystal layer also exports compact top-level crystal `results` for inspection, while scans and heavy arrays belong in `debug_data`.

## Practical Notes

- `phase_matching` and `double_resonance` do not generally coincide.
- In `double_resonance` mode, the selected crystal length may differ from the cavity file.
- When that happens, OPO requires the cavity workflow to be rerun with the selected crystal length.

For the execution order, see [02_workflow.md](02_workflow.md). For the JSON structure, see [04_outputs.md](04_outputs.md).
