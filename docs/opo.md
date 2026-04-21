# OPO Layer

This page documents the current OPO-side workflow and inputs.

## Role

The OPO layer consumes cavity and crystal exports and builds the current below-threshold operating-point and squeezing workflow.

The entry point is:

- `src/opo/opo_main.py`

## What `opo_main.py` Does

The OPO script:

- loads cavity and crystal JSON outputs
- checks crystal-length consistency between the selected crystal operating point and the loaded cavity geometry
- builds the OPO operating-point model
- builds the Langevin scaffold
- computes squeezing spectra
- generates the OPO plots
- writes the OPO JSON

## Crystal Inputs It Consumes

The OPO layer uses:

- cavity `results`
- crystal `results.active_for_opo`

In particular it reads from `active_for_opo`:

- `temperature_K`
- `crystal_length_m`
- `phase_matching`
- `mode_matching`
- `boyd_kleinman_analysis`
- `polarization_resonance`

This keeps the model, summary, and resonance plot tied to the same selected operating point.

## OPO Operating-Point Model

The current operating-point model uses:

- cavity `kappa_ext_Hz`
- cavity `kappa_loss_Hz`
- cavity `kappa_total_Hz`
- cavity `escape_efficiency`
- crystal nonlinear overlap and effective coupling inputs
- crystal active temperature and crystal length

Detection efficiency is treated separately from cavity escape physics.

## Plots

The current OPO plotting layer generates:

- squeezing spectrum
- longitudinal resonance diagnostic

The resonance diagnostic uses the active crystal polarization-resonance block when available.

## Scope

The current OPO model is intentionally simplified.

It is:

- below threshold
- degenerate
- compact and operating-point oriented

It is not:

- a full non-degenerate model
- a multimode model
- a full first-principles threshold model

For the physical scope of the model, see [physics.md](physics.md). For the output structure, see [outputs.md](outputs.md).
