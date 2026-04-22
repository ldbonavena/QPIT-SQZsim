# OPO Layer

This page documents the OPO-side workflow and the final simulation stage of the pipeline.

## Role

The OPO layer consumes the cavity and crystal outputs and builds the final operating-point model used to compute squeezing spectra.

It combines:

- cavity loss and linewidth (kappa)
- crystal nonlinear interaction
- operating-point selection from the crystal layer
- a linearized Langevin model for quantum noise

The entry point is:

- `src/opo/opo_main.py`

## What `opo_main.py` Does

The OPO script:

- loads cavity and crystal JSON outputs
- validates consistency between cavity and crystal operating point
- builds the OPO operating-point model
- constructs the Langevin model
- computes squeezing spectra
- generates diagnostic plots
- exports results to JSON

## Workflow

The OPO layer performs the following steps:

1. Load cavity and crystal outputs
2. Validate crystal–cavity consistency
3. Build OPO parameters
4. Derive the OPO operating-point model
5. Construct the Langevin model (quadrature basis)
6. Compute frequency-domain squeezing spectra
7. Build structured output
8. Generate plots and save results

## Inputs from Cavity and Crystal

The OPO layer consumes:

### From cavity (`results`)

- `kappa_ext_Hz`
- `kappa_loss_Hz`
- `kappa_total_Hz`
- `escape_efficiency`
- cavity detuning

### From crystal (`results.active_for_opo`)

- `operating_point_mode`
- `temperature_K`
- `crystal_length_m`
- `phase_matching`
- `mode_matching`
- `boyd_kleinman_analysis`
- `polarization_resonance`

The `active_for_opo` block is the **single source of truth** for the crystal state.

## Consistency Check

The OPO layer enforces consistency between:

- cavity crystal length
- crystal selected operating-point length

If these differ (e.g. after a double-resonance scan):

- the simulation stops
- the user must rerun the cavity with the updated crystal length

This prevents mixing incompatible geometry and nonlinear calculations.

## OPO Operating-Point Model

The OPO model combines cavity and crystal physics into a compact set of parameters:

- pump parameter `σ`
- effective threshold power
- nonlinear coupling
- escape efficiency
- cavity linewidth and detuning

The nonlinear coupling depends on:

- `d_eff`
- crystal length
- spatial mode overlap
- effective mode area

The threshold is not a full first-principles calculation, but a **physics-informed approximation** calibrated around the provided threshold power.

## Langevin Model

The current implementation uses a **linearized 2×2 quadrature model**.

It defines:

- quadratures: X and P
- drift matrix (including damping and detuning)
- input and noise coupling matrices

Key features:

- valid only **below threshold**
- includes quadrature mixing via cavity detuning
- provides a minimal but consistent noise model

## Squeezing Spectrum

The squeezing calculation:

- evaluates the frequency-domain response of the Langevin model
- computes spectral densities for X and P quadratures
- identifies squeezing and anti-squeezing
- includes:

  - escape efficiency (intracavity → output)
  - detection efficiency (measurement loss)

Outputs include:

- squeezing spectrum
- anti-squeezing spectrum
- measured quadrature spectrum (LO phase dependent)
- optimal squeezing phase vs frequency

All spectra are normalized to the high-frequency shot-noise limit.

## Resonance Diagnostic

The OPO layer provides a visualization of longitudinal resonances:

- signal and idler mode combs
- cavity linewidth
- gain envelope

This is based on:

- `polarization_resonance` from the crystal layer

It is a **diagnostic visualization**, not a full transfer-function model.

## Outputs

The OPO JSON output is structured as:

- `inputs`: simulation parameters and file references
- `results`:
  - `model`: compact OPO operating-point quantities
  - `spectrum`: squeezing spectra
- `debug_data`:
  - Langevin matrices and internal diagnostics

The `model` block includes:

- pump parameter
- threshold powers
- cavity decay rates
- escape efficiency
- crystal operating point (mode, temperature, length)

For the full schema, see [04_outputs.md](../04_outputs.md).

## Scope

The current OPO model is intentionally limited.

It is:

- below threshold
- degenerate
- single-mode
- linearized (Gaussian)

It is not:

- a full non-degenerate model
- a multimode model
- a full nonlinear (above-threshold) model
- a complete first-principles threshold calculation

## Practical Notes

- squeezing depends strongly on escape efficiency and detection efficiency
- cavity detuning rotates the squeezing quadrature
- the selected crystal operating point directly affects the OPO performance
- double-resonance operation requires cavity–crystal consistency

For execution order, see [02_workflow.md](../02_workflow.md).  
For architecture, see [01_architecture.md](../01_architecture.md).  
For physical background, see [03_physics.md](../03_physics.md).