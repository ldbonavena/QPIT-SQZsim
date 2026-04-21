# 02 — Workflow

The simulator is meant to run in three explicit steps:

1. `cavity_main.py`
2. `crystal_main.py`
3. `opo_main.py`

Each step writes a JSON file used by the next one.

## 1. Cavity

`src/cavity/cavity_main.py` defines the cavity configuration and computes:

- geometry-dependent mode properties
- beam waist in the crystal
- free spectral range
- reflectivity-based loss quantities
- `kappa_ext_Hz`, `kappa_loss_Hz`, `kappa_total_Hz`
- `escape_efficiency`

## 2. Crystal

`src/crystal/crystal_main.py` loads the cavity JSON and then:

- computes the phase-matching scan
- computes the phase-matching resonance diagnostic
- optionally computes the double-resonance scan
- builds candidate operating points
- selects the active operating point from `OPERATING_POINT_MODE`
- evaluates the active crystal quantities at that selected point
- exports `results.active_for_opo`

The current operating-point modes are:

- `phase_matching`
- `double_resonance`

## 3. OPO

`src/opo/opo_main.py` loads cavity and crystal outputs and then:

- validates that the selected crystal length matches the loaded cavity geometry
- builds the below-threshold OPO operating-point model
- builds the Langevin scaffold
- computes squeezing spectra
- generates the OPO plots

## Why The Order Matters

The layers are not independent.

- The crystal layer depends on the cavity beam waist and cavity geometry.
- The OPO layer depends on cavity loss quantities and the crystal active operating point.

If the cavity and crystal files refer to different crystal lengths, OPO stops with an explicit error instead of silently mixing inconsistent states.

## When To Rerun Cavity

You must rerun `cavity_main.py` when the selected crystal operating point changes the active crystal length.

Typical case:

- `OPERATING_POINT_MODE = "double_resonance"`
- the selected double-resonance point has `crystal_length_m` different from `cavity.inputs.crystal_length_m`

In that case, rerun:

1. `python src/cavity/cavity_main.py`
2. `python src/crystal/crystal_main.py`
3. `python src/opo/opo_main.py`

For the module-specific details of each stage, see [cavity.md](cavity.md), [crystal.md](crystal.md), and [opo.md](opo.md).
