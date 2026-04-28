# QPIT-SQZsim

QPIT-SQZsim is a staged simulation framework for an optical parametric oscillator (OPO). It links cavity design, nonlinear-crystal operating-point selection, and below-threshold squeezing spectra in one reproducible pipeline.

```text
cavity -> crystal -> OPO
```

## What It Does

- **Cavity**: computes resonator geometry, Gaussian mode size in the crystal, round-trip lengths, losses, decay rates, and escape efficiency.
- **Crystal**: computes refractive indices, phase matching, QPM poling, double-resonance diagnostics, operating-point selection, and nonlinear spatial overlap.
- **OPO**: consumes the cavity and crystal outputs, computes a physical threshold, builds a below-threshold degenerate Langevin model, and exports squeezing spectra.

## Quick Start

Install dependencies, then run the stages in order:

```bash
pip install -r requirements.txt

python src/cavity/cavity_main.py
python src/crystal/crystal_main.py
python src/opo/opo_main.py
```

Each stage writes JSON and plots under:

```text
results/<geometry>/cavity/
results/<geometry>/crystal/
results/<geometry>/opo/
```

The next stage reads the JSON produced by the previous stage, so rerun downstream stages after changing upstream configuration.

## Current OPO Scope

The OPO layer currently models a:

- below-threshold OPO
- degenerate signal/idler case
- single spatial/longitudinal mode
- linearized quadrature Langevin model

The current implementation does not include pump depletion, above-threshold dynamics, multimode dynamics, or a full non-degenerate OPO model.

## Documentation

- [Overview](docs/00_overview.md)
- [Architecture](docs/01_architecture.md)
- [Workflow](docs/02_workflow.md)
- [Physics](docs/03_physics.md)
- [Outputs](docs/04_outputs.md)
- [Cavity module](docs/modules/cavity.md)
- [Crystal module](docs/modules/crystal.md)
- [OPO module](docs/modules/opo.md)
