# Crystal Layer

This page documents the crystal-side workflow and the crystal → OPO interface.

## Role

The crystal layer consumes the cavity output and defines the nonlinear interaction and operating point used by the OPO layer.

It combines:

- phase matching (Δk physics)
- spatial mode matching (Boyd–Kleinman)
- cavity resonance constraints, especially for Type II interactions

The entry point is:

- `src/crystal/crystal_main.py`

## What `crystal_main.py` Does

The crystal script:

- loads the cavity JSON output
- resolves the crystal material model and interaction type
- computes the phase-matching scan
- evaluates the resonance diagnostic at the phase-matching point
- optionally computes the double-resonance scan
- builds candidate operating points
- selects one active operating point
- evaluates active crystal quantities at that point
- exports the crystal JSON and plots

## Workflow

The crystal layer performs the following steps:

1. Load cavity output (geometry, waist, losses, and cavity-derived quantities)
2. Select a refractive-index model and phase-matching type
3. Compute phase matching versus temperature
4. Evaluate the resonance diagnostic at the phase-matching operating point
5. Optionally perform a double-resonance scan over temperature and crystal length
6. Build candidate operating points
7. Select one operating point using `OPERATING_POINT_MODE`
8. Evaluate active crystal quantities at that point
9. Export the crystal results for downstream OPO use

## Phase Matching

The phase-matching module computes:

- refractive indices for pump, signal, and idler
- three-wave mismatch:
  
  `Δk = k_p − k_s − k_i`

- quasi-phase-matching correction:

  `Δk_eff = Δk − m · (2π / Λ)`

- phase-matching power factor:

  `sinc²(Δk_eff · L / 2)`

The main output is a temperature scan containing quantities such as:

- `pm_power`
- `delta_k_eff`
- `T_best_K`

This defines the phase-matching operating point.

## Double Resonance

For polarization non-degenerate cases, especially Type II, signal and idler must both satisfy cavity resonance conditions.

The resonance diagnostic evaluates:

- signal round-trip phase
- idler round-trip phase
- wrapped phase mismatch:

  `Δφ_wrapped ∈ [-π, π]`

The double-resonance condition is:

- `Δφ_wrapped ≈ 0`

The optional scan explores:

- temperature
- crystal length

and identifies the best double-resonant operating point.

Typical outputs include:

- best temperature
- best crystal length
- residual wrapped phase mismatch
- double-resonance status

## Operating-Point Logic

The active operating point is selected via:

- `OPERATING_POINT_MODE`

Supported modes are:

- `phase_matching`  
  selects the point that maximizes nonlinear conversion (`Δk_eff ≈ 0`)

- `double_resonance`  
  selects the point that minimizes wrapped signal/idler phase mismatch (`Δφ_wrapped ≈ 0`)

These two conditions generally do not coincide.

The selected point is exported as:

- `results.selected_operating_point_mode`
- `results.selected_operating_point`

## Boyd–Kleinman Analysis

The crystal layer evaluates the spatial overlap efficiency using a Boyd–Kleinman description.

The main control parameters are:

- focusing parameter: `ξ = L / (2 z_R)`
- mismatch parameter: `σ = z_R · Δk_eff`

The BK factor `h_BK(σ, ξ)` is used to quantify how well the cavity mode overlaps the nonlinear interaction.

Outputs include:

- the BK value at the operating point
- the optimal BK reference point
- a comparison between the actual and optimal focusing condition

This is the main spatial-overlap diagnostic used by the crystal layer.

## `active_for_opo`

The main OPO-facing crystal block is:

- `results.active_for_opo`

It contains the resolved crystal state at the selected operating point, including:

- operating-point mode
- temperature
- crystal length
- phase matching
- mode matching
- Boyd–Kleinman analysis
- polarization resonance

This is the single source of truth for the OPO layer.

## Interface to the OPO Layer

The OPO layer consumes:

- `active_for_opo.phase_matching`
- `active_for_opo.mode_matching`
- `active_for_opo.boyd_kleinman_analysis`
- `active_for_opo.polarization_resonance`
- `active_for_opo.temperature_K`
- `active_for_opo.crystal_length_m`

These define:

- nonlinear coupling strength
- spatial overlap
- resonance condition
- active operating temperature
- active crystal length

The OPO layer should use `active_for_opo` consistently rather than reinterpreting crystal results independently.

## Consistency with the Cavity

In `double_resonance` mode, the selected crystal length may differ from the one used in the cavity simulation.

When this happens:

- the cavity must be recomputed with the new crystal length
- otherwise the crystal and OPO layers become inconsistent with the loaded cavity geometry

The current workflow enforces this with an explicit consistency check before OPO simulation.

## Outputs

The crystal JSON output is structured as:

- `inputs`: configuration and selected models
- `results`: compact quantities used downstream
- `debug_data`: scans, maps, and detailed diagnostics

The `results` block contains the compact OPO-facing interface.

The `debug_data` block may contain:

- phase-matching scans
- double-resonance scans
- BK maps
- other heavy arrays used for visualization or debugging

For the general JSON layout, see [04_outputs.md](../04_outputs.md).

## Practical Notes

- phase matching and double resonance are distinct optimization targets
- Type II interactions require explicit resonance tuning
- the crystal layer does not modify cavity geometry automatically
- the crystal → OPO handoff is mediated by `active_for_opo`

For execution order, see [02_workflow.md](../02_workflow.md).  
For high-level architecture, see [01_architecture.md](../01_architecture.md).  
For the physical model, see [03_physics.md](../03_physics.md).