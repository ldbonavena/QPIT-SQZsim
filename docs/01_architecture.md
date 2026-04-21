# 01 — Architecture

The project is organized as a one-way pipeline:

`cavity -> crystal -> OPO`

Each layer owns one part of the model and exports the quantities needed downstream.

## Cavity Layer

The cavity layer defines:

- geometry
- Gaussian resonator mode properties
- resonant loss model
- derived loss and coupling quantities such as `kappa_ext_Hz`, `kappa_loss_Hz`, `kappa_total_Hz`
- `escape_efficiency`

It is the only layer that computes cavity losses and coupling rates.

## Crystal Layer

The crystal layer defines:

- refractive-index and phase-matching calculations
- phase-matching and double-resonance operating-point candidates
- the selected operating point
- mode-matching quantities
- Boyd-Kleinman summary data
- polarization-resonance diagnostics

Its downstream handoff is:

- `crystal.results.active_for_opo`

This is the resolved crystal state intended for OPO.

## OPO Layer

The OPO layer consumes:

- cavity `results`
- crystal `results.active_for_opo`

It builds:

- a compact below-threshold operating-point model
- a minimal Langevin scaffold
- squeezing and anti-squeezing spectra
- OPO plots

The OPO layer is a consumer. It should not reinterpret cavity geometry or crystal operating-point selection.

## Data Flow

The JSON outputs are the interface between layers.

- `cavity` exports geometry-dependent mode and loss quantities.
- `crystal` loads the cavity JSON and exports one resolved active operating point.
- `opo` loads both cavity and crystal JSON and uses them directly.

This keeps the layer boundaries explicit:

- geometry and losses live in `cavity`
- nonlinear operating-point selection lives in `crystal`
- quantum-noise and squeezing calculations live in `opo`

For the detailed run order, see [02_workflow.md](02_workflow.md). For the JSON interface, see [04_outputs.md](04_outputs.md).
