# Overview

QPIT-SQZsim models the optical chain needed to analyze an Optical Parametric Oscillator from cavity geometry up to quantities that matter for squeezing. The current implementation covers the linear cavity eigenmode problem, the crystal-layer calculations that depend on that mode, and a compact below-threshold degenerate OPO/squeezing layer.

## Physical Scope

The code solves a staged problem:

1. Build the resonator round-trip optics from a chosen cavity geometry.
2. Extract the stable Gaussian eigenmode inside the cavity crystal region.
3. Use that intracavity mode to evaluate crystal phase matching and focused-beam overlap.
4. Use the exported cavity and crystal results to build a compact below-threshold OPO model and squeezing spectra.

In that sense, the project pipeline is:

`cavity -> crystal -> OPO -> squeezing`

The current implementation covers all four layers in a compact staged form, while leaving room for richer future models.

## Conceptual Module Interaction

The `cavity` layer answers: what mode does the resonator support, and what are its linear dynamical parameters? It produces beam waists, `q` parameters, round-trip length, decay rates, Gouy phases, and detuning-related quantities.

The `crystal` layer answers: given that cavity mode, what crystal operating point and QPM period are required, and how well does the nonlinear medium support the intended interaction? It computes refractive-index-dependent phase matching, derives a design poling period when requested, determines the operating temperature, and evaluates focused-beam overlap through a Boyd-Kleinman-style model.

The `opo` layer combines cavity loss, coupling, detuning, and crystal-derived nonlinear interaction strength into a compact below-threshold operating-point model, a 2x2 quadrature Langevin model, and frequency-domain squeezing spectra.

## Why the Separation Matters

The main design choice is to keep resonator optics, crystal physics, and future quantum/OPO dynamics loosely coupled. Each layer consumes a compact result from the previous one instead of reaching directly into internal functions. That makes the physical pipeline explicit:

- cavity geometry determines the intracavity Gaussian mode
- the Gaussian mode determines nonlinear overlap in the crystal
- cavity linewidth and detuning determine the frequency response seen by the OPO model

The `docs/architecture.md`, `docs/cavity.md`, `docs/crystal.md`, and `docs/opo.md` files expand these layers in more detail.
