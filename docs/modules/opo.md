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

## Initial Configuration

The OPO workflow is driven mainly by the parameters defined in `opo_main.py`.

The most important ones are:

- `pump_power_W`
- `threshold_power_W`
- `signal_wavelength_m`
- `pump_wavelength_m`
- `analysis_sideband_Hz`
- `analysis_span_Hz`
- `n_analysis_points`
- `detection_efficiency`
- `lo_phase_rad`

These define the operating regime, the analysis frequency range, and the measurement conditions.

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

The OPO layer does not choose the operating point itself. It uses the point already selected by the crystal layer.

## Consistency Check

The OPO layer enforces consistency between:

- cavity crystal length
- crystal selected operating-point length

If these differ (for example after a double-resonance scan):

- the simulation stops
- the cavity must be rerun with the updated crystal length

This prevents mixing incompatible cavity geometry and crystal operating conditions.

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

## Reading the OPO Summary

The OPO summary provides the main operating-point quantities.

Typical interpretation:

- `pump parameter sigma`  
  normalized pump strength relative to threshold

- `effective threshold power`  
  threshold estimate including the current cavity/crystal operating conditions

- `below_threshold`  
  whether the model is being used in its intended regime

- `crystal operating point mode`  
  whether the crystal layer selected `phase_matching` or `double_resonance`

- `crystal active temperature` and `crystal active length`  
  the actual crystal state used by the OPO model

## Resonance Diagnostic

The OPO layer provides a visualization of longitudinal resonances:

- signal and idler mode combs
- cavity linewidth
- gain envelope

This is based on the crystal-side polarization-resonance diagnostic.

It is a **diagnostic visualization**, not a full transfer-function model.

## How to Use the OPO Plots

The OPO plots are diagnostic and interpretive tools.

Typical usage:

1. Inspect the squeezing spectrum to evaluate the predicted noise reduction
2. Inspect the measured quadrature trace to understand the effect of LO phase
3. Inspect the resonance diagnostic to see whether signal and idler are close to simultaneous resonance
4. Compare results for different crystal operating-point modes if needed

The resonance plot is especially useful for checking whether a `double_resonance` operating point is being used consistently.

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
- changing the crystal operating point does not automatically change cavity geometry

For execution order, see [02_workflow.md](../02_workflow.md).  
For architecture, see [01_architecture.md](../01_architecture.md).  
For physical background, see [03_physics.md](../03_physics.md).