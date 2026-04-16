# OPO Module

## Overview

The OPO layer takes the exported cavity and crystal results and builds a compact below-threshold degenerate OPO model. In the current pipeline,

`cavity -> crystal -> OPO -> spectrum`

the cavity layer provides linewidth, detuning, and escape efficiency, the crystal layer provides nonlinear-overlap information, and the OPO layer combines those inputs into an operating-point model, a 2x2 quadrature Langevin model, and frequency-domain squeezing spectra.

## Operating-Point Model

The current operating-point model is physics-informed but still intermediate. It does not yet attempt a full absolute threshold derivation from first principles.

The model separates the threshold estimate into:

- a baseline threshold power: the user-supplied engineering calibration parameter `threshold_power_W`
- a crystal-derived nonlinear coupling proxy: taken from `mode_matching["effective_nonlinear_overlap"]` when available, otherwise from `boyd_kleinman_analysis["reference"]["bk_reference_factor"]`, otherwise from a unity fallback
- a cavity-loss scaling term: derived from cavity linewidth and escape efficiency

From these ingredients the code builds:

- `effective_nonlinear_coupling`
- `cavity_loss_scale`
- `effective_threshold_power_W`
- the pump parameter `sigma`

The qualitative behavior is intentional:

- stronger nonlinear overlap lowers the effective threshold
- higher cavity loss raises the effective threshold
- the user input still sets the overall watt scale

This keeps the OPO operating point tied to upstream cavity/crystal results while remaining compact and easy to calibrate.

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
