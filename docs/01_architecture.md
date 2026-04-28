# 01 - Architecture

The codebase is split into four source areas:

```text
src/cavity/   resonator geometry, Gaussian mode, losses
src/crystal/  refractive index, phase matching, operating point, BK overlap
src/opo/      physical threshold, pump parameter, Langevin model, spectra
src/common/   constants and results-path helpers
```

The data flow is one-way:

```text
cavity JSON -> crystal JSON -> OPO JSON
```

## Cavity Layer

The cavity layer owns all resonator geometry and resonant-field loss calculations. It computes:

- geometric and optical round-trip lengths
- beam waist in the crystal
- free spectral range
- output-coupling and internal-loss decay rates
- total decay rate and escape efficiency
- Gouy phases and ABCD diagnostics

Downstream stages use these values as exported. They do not recompute cavity geometry.

## Crystal Layer

The crystal layer consumes the cavity JSON and owns the nonlinear operating point. It computes:

- material refractive indices
- QPM phase matching and optional design poling period
- phase-matching and double-resonance operating-point candidates
- selected operating point
- mode matching and Boyd-Kleinman overlap
- compact `active_for_opo` handoff payload

The OPO layer uses `results.active_for_opo` as the resolved crystal state.

## OPO Layer

The OPO layer consumes cavity and crystal JSON files. It computes:

- physical threshold from cavity decay rates and crystal nonlinear parameters
- pump operating point from either sigma/fraction mode or absolute pump power
- below-threshold 2x2 quadrature Langevin model
- squeezing, anti-squeezing, measured quadrature, and optimal phase spectra

It validates that the selected crystal length is consistent with the loaded cavity geometry.

## Common Layer

`src/common/` contains shared physical constants and helpers for locating `results/<geometry>/<stage>/` output directories.
