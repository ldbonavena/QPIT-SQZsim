# OPO Module

## Overview

The OPO layer takes the exported cavity and crystal results and builds a compact below-threshold degenerate OPO model. In the current pipeline,

`cavity -> crystal -> OPO -> spectrum`

the cavity layer provides linewidth, detuning, and escape efficiency, the crystal layer provides the resolved nonlinear interaction data and focused-beam overlap information, and the OPO layer combines those inputs into an operating-point model, a 2x2 quadrature Langevin model, and frequency-domain squeezing spectra.

## Operating-Point Model

The current operating-point model is physics-informed but still intermediate. It does not yet attempt a full absolute threshold derivation from first principles.

The model separates the threshold estimate into:

- a baseline threshold power: the user-supplied engineering calibration parameter `threshold_power_W`
- a crystal-derived nonlinear coupling estimate built from:
  - the exported effective nonlinearity `d_eff`
  - the crystal length `L`
  - an overlap-like factor from mode matching, with fallback to the BK reference factor when needed
  - an effective mode area `A_eff`
- a cavity-loss scaling term: derived from cavity linewidth and escape efficiency

From these ingredients the code builds:

- `effective_nonlinear_coupling`
- `cavity_loss_scale`
- `effective_threshold_power_W`
- the pump parameter `sigma`

The present coupling estimate follows the explicit intermediate scaling

`g_eff ∝ d_eff · L · overlap / sqrt(A_eff)`

where:

- `d_eff` is the crystal effective nonlinearity resolved upstream by the crystal layer
- `L` is the crystal length used for the nonlinear interaction
- `overlap` is the effective nonlinear-overlap factor exported by the crystal workflow, with BK-based fallback when direct mode-matching overlap is unavailable
- `A_eff` is the effective mode area built from the crystal waist

The qualitative behavior is intentional:

- larger `d_eff`, longer crystal length, and stronger overlap increase the effective nonlinear coupling
- larger mode area weakens the effective nonlinear coupling
- higher cavity loss raises the effective threshold
- the user input still sets the overall watt scale

This keeps the OPO operating point tied to upstream cavity/crystal results while remaining compact and easy to calibrate.

## Effective Mode Area

For the current Phase B coupling model, the effective mode area is approximated by

`A_eff ≈ π w_0^2`

with `w_0` the beam waist inside the crystal. The OPO layer prefers the crystal waist exported by `mode_matching["waist_crystal_m"]`, falls back to `inputs["beam_waist_crystal_m"]`, and only uses a simple fixed fallback if neither value is available.

This area estimate is sufficient for the current intermediate coupling model because it captures the intended qualitative behavior: tighter focusing increases the nonlinear interaction strength, while larger mode size reduces it.

## Data Flow

The OPO layer does not compute crystal material properties itself.

- `src/crystal/crystal_materials.py` resolves the interaction-type-dependent `d_eff`
- the crystal workflow exports `d_eff`, crystal geometry, and overlap-related quantities in the crystal JSON
- `src/opo/opo_model.py` reads those exported quantities and builds the effective nonlinear coupling and threshold estimate

This keeps crystal-material details inside the crystal layer and lets the OPO layer operate only on structured outputs from upstream simulations.

## Threshold Model

The current threshold model is a compact physics-informed formulation and not yet a full first-principles derivation.

It combines:

- cavity-loss scaling from cavity linewidth and escape efficiency
- the effective nonlinear coupling built from `d_eff`, crystal length, overlap, and mode area
- the user-supplied calibration threshold `threshold_power_W`, which still sets the engineering watt scale

Stronger nonlinear coupling lowers the effective threshold, while higher cavity loss raises it. This is sufficient for the present staged workflow, but it should still be interpreted as an intermediate model rather than as a complete absolute threshold calculation.

## Langevin Quadrature Model

The current Langevin model is a 2x2 single-mode quadrature model in the `(X, P)` basis.

Its role is to provide a minimal linearized dynamical description for a below-threshold degenerate OPO. In this model:

- the diagonal drift-matrix terms represent quadrature damping modified by the pump parameter `sigma`
- the off-diagonal drift-matrix terms represent quadrature mixing through cavity detuning

The cavity linewidth sets the dynamical bandwidth of the response, while cavity detuning rotates and mixes the quadratures. This is why the OPO output is naturally treated as a quadrature spectral-density matrix rather than as two unrelated scalar channels.

## Squeezing Spectrum

The OPO spectrum is computed in the frequency domain from the Langevin response. For each analysis frequency, the code builds a 2x2 quadrature output spectral-density matrix from the linear response of the current Langevin model.

All reported spectra are derived from that same matrix:

- the `X` quadrature spectrum
- the `P` quadrature spectrum
- the inferred squeezing spectrum
- the inferred anti-squeezing spectrum
- the measured quadrature spectrum for a chosen LO phase

The current implementation normalizes each quadrature projection to its high-frequency asymptote so that the spectra approach shot noise at large analysis frequency. After that normalization, the model applies:

- escape efficiency
- detection efficiency

phenomenologically as output losses.

## Homodyne Detection (LO Phase)

The OPO layer supports homodyne measurement of an arbitrary quadrature defined by the LO phase `theta = lo_phase_rad`.

The measured quadrature is

`X_theta = X cos(theta) + P sin(theta)`

and its spectrum is exported as `measured_quadrature_spectrum`.

The code also exports `optimal_phase_rad`, which stores the phase of the minimum-noise quadrature at each analysis frequency. This is obtained from the eigendecomposition of the same 2x2 quadrature spectral matrix used for the other spectra.

In the current interpretation:

- the squeezing spectrum is the lower-noise quadrature identified from the low-frequency ordering
- the anti-squeezing spectrum is the orthogonal higher-noise quadrature
- the measured spectrum is the homodyne spectrum at the user-selected LO phase

## Limitations

The current OPO implementation is intentionally compact and should be interpreted with those limits in mind:

- below-threshold only: `sigma < 1`
- degenerate OPO only
- 2x2 single-mode quadrature model
- simplified noise coupling and output relation
- not yet a full quantum input-output treatment
- not yet a multimode, covariance-propagation, or full measurement-chain model

Within those limits, the current OPO layer is useful for rapid exploration and for keeping the cavity, crystal, and squeezing stages connected through one consistent staged workflow.
