# QPIT-SQZsim

QPIT-SQZsim is a simulation framework for designing and analyzing optical parametric oscillators (OPOs), with a focus on cavity design, nonlinear crystal operation, and below-threshold squeezing performance.

The project is structured as a modular pipeline:

cavity → crystal → OPO

---

## What this project does

This framework allows you to:

- Design optical cavities and evaluate resonator properties and losses
- Compute phase matching and double-resonance conditions in nonlinear crystals
- Select physically consistent operating points
- Simulate below-threshold OPO behavior and squeezing spectra

---

## Simulation Pipeline

The simulation is performed in three sequential steps:

```
cavity
   ↓
crystal
   ↓
OPO
```

- **Cavity**: computes geometry, mode size, FSR, and loss rates (kappa, escape efficiency)
- **Crystal**: computes phase matching and double resonance, and selects the active operating point
- **OPO**: builds the operating-point model and computes squeezing spectra

Each stage consumes the output of the previous one.

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd QPIT-SQZsim
```

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional (editable install):

```bash
pip install -e .
```

---

## Quick Start

Run the full simulation pipeline:

```bash
python src/cavity/cavity_main.py
python src/crystal/crystal_main.py
python src/opo/opo_main.py
```

Each step depends on the outputs produced by the previous one.

---

## Project Structure

Main modules:

- `src/cavity` — cavity geometry, mode properties, and loss model
- `src/crystal` — phase matching, double resonance, and operating-point selection
- `src/opo` — OPO model, Langevin equations, and squeezing spectra

For detailed concepts and definitions, see the documentation in the `docs/` directory.

---

## Outputs

Each stage writes results to disk (JSON + plots). These outputs are used as inputs for the next stage in the pipeline.

---

## Documentation

High-level documentation:

- [Overview](docs/00_overview.md)
- [Architecture](docs/01_architecture.md)
- [Workflow](docs/02_workflow.md)
- [Physics](docs/03_physics.md)
- [Outputs](docs/04_outputs.md)

Module-specific documentation:

- [Cavity](docs/modules/cavity.md)
- [Crystal](docs/modules/crystal.md)
- [OPO](docs/modules/opo.md)

---

## Notes

- The current OPO model is:
  - below-threshold
  - degenerate
  - single-mode

- Full non-degenerate and multimode dynamics are not yet implemented.