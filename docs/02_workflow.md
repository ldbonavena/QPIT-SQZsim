# 02 — Workflow

This section describes how to run the simulator and how data flows through the pipeline.

The simulation is executed in three sequential steps:

cavity → crystal → OPO

Each step writes a JSON file that is used as input by the next one.

## 1. Cavity

`src/cavity/cavity_main.py` defines the cavity configuration and computes:

- geometry-dependent mode properties
- beam waist in the crystal
- free spectral range (FSR)
- reflectivity-based loss quantities
- `kappa_ext_Hz`, `kappa_loss_Hz`, `kappa_total_Hz`
- `escape_efficiency`

The output JSON defines the **optical system and loss model** used by all downstream layers.

## 2. Crystal

`src/crystal/crystal_main.py` loads the cavity JSON and then:

- computes the phase-matching scan
- evaluates the phase-matching resonance diagnostic
- optionally computes the double-resonance scan
- builds candidate operating points
- selects the active operating point using `OPERATING_POINT_MODE`
- evaluates all crystal quantities at that selected point
- exports `results.active_for_opo`

The current operating-point modes are:

- `phase_matching`
- `double_resonance`

The output defines the **nonlinear operating point** used by the OPO layer.

## 3. OPO

`src/opo/opo_main.py` loads cavity and crystal outputs and then:

- validates consistency between cavity geometry and crystal operating point
- builds the below-threshold OPO operating-point model
- constructs the Langevin model
- computes squeezing spectra
- generates plots

The output contains the **final physical prediction** of the simulation.

## Data Flow

The workflow enforces a strict data flow:

- `cavity` → defines geometry and losses  
- `crystal` → defines the operating point  
- `opo` → computes quantum noise and squeezing  

Each layer consumes the output of the previous one and does not modify upstream quantities.

## Why the Order Matters

The layers are not independent:

- the crystal layer depends on the cavity beam waist and loss model  
- the OPO layer depends on both cavity losses and the crystal operating point  

Running the steps out of order leads to inconsistent results.

## When to Rerun Cavity

You must rerun `cavity_main.py` when the selected crystal operating point changes the crystal length.

Typical case:

- `OPERATING_POINT_MODE = "double_resonance"`
- the selected point has a different `crystal_length_m` than the one used in the cavity

In that case, rerun:

1. `python src/cavity/cavity_main.py`
2. `python src/crystal/crystal_main.py`
3. `python src/opo/opo_main.py`

This ensures that cavity geometry and crystal operating point remain consistent.

---

For module-specific details, see:

- [cavity.md](modules/cavity.md)
- [crystal.md](modules/crystal.md)
- [opo.md](modules/opo.md)