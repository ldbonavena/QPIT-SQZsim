# QPIT-SQZsim

`QPIT-SQZsim` is a layered simulator for cavity geometry, nonlinear crystal operating points, and a compact below-threshold OPO model for squeezing studies.

The pipeline is:

`cavity -> crystal -> OPO`

- The cavity layer computes geometry-dependent mode properties and resonant loss rates.
- The crystal layer computes phase matching, double resonance, and the selected active operating point.
- The OPO layer consumes those exported quantities and builds the operating-point model, Langevin scaffold, and squeezing spectra.

## Installation

```bash
git clone <repository-url>
cd QPIT-SQZsim
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional editable install:

```bash
pip install -e .
```

## Quick Start

Run the simulation pipeline in order:

```bash
python src/cavity/cavity_main.py
python src/crystal/crystal_main.py
python src/opo/opo_main.py
```

Each step depends on the outputs produced by the previous one.

## Source Layout

Main source directories:

- `src/cavity`: cavity geometry, resonator mode, and loss model
- `src/crystal`: phase matching, double resonance, operating-point selection, and nonlinear overlap
- `src/opo`: below-threshold OPO model, Langevin scaffold, and squeezing spectra
- `src/common`: shared utilities such as results-path helpers

Crystal module files:

- `crystal_main.py`
- `crystal_workflow.py`
- `crystal_materials.py`
- `crystal_phase_matching.py`
- `crystal_mode_matching.py`
- `crystal_boyd_kleinman.py`
- `crystal_double_resonance_scan.py`
- `crystal_polarization_resonance.py`
- `crystal_plotter.py`

## Key Concepts

- `operating_point_mode`: the crystal-side rule used to select the active operating point. The current choices are `phase_matching` and `double_resonance`.
- `escape_efficiency`: the cavity output-coupling fraction, `kappa_ext_Hz / kappa_total_Hz`.
- Below-threshold OPO model: the current OPO layer is a compact degenerate below-threshold model intended for operating-point studies and squeezing spectra, not full multimode or non-degenerate dynamics.

## Documentation

High-level docs:

- [Overview](docs/00_overview.md)
- [Architecture](docs/01_architecture.md)
- [Workflow](docs/02_workflow.md)
- [Physics](docs/03_physics.md)
- [Outputs](docs/04_outputs.md)

Per-layer docs:

- [Cavity](docs/cavity.md)
- [Crystal](docs/crystal.md)
- [OPO](docs/opo.md)
