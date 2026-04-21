# 00 — Overview

This documentation is split into two layers:

- conceptual docs for the overall pipeline and interfaces
- per-layer docs for the cavity, crystal, and OPO modules

## Documentation order

1. Overview -> `docs/00_overview.md`
2. Architecture -> `docs/01_architecture.md`
3. Workflow -> `docs/02_workflow.md`
4. Physics -> `docs/03_physics.md`
5. Outputs -> `docs/04_outputs.md`

Module-specific documentation:

- Cavity -> `docs/cavity.md`
- Crystal -> `docs/crystal.md`
- OPO -> `docs/opo.md`

## Conceptual Docs

- [01_architecture.md](01_architecture.md): project structure, layer boundaries, and the cavity -> crystal -> OPO data flow
- [02_workflow.md](02_workflow.md): execution order, rerun conditions, and how the staged workflow is used in practice
- [03_physics.md](03_physics.md): high-level physical model, including cavity losses, phase matching, double resonance, and the current OPO scope
- [04_outputs.md](04_outputs.md): JSON structure and downstream-facing result interfaces

## Per-Layer Docs

- [cavity.md](cavity.md): cavity-layer inputs, supported geometries, exported loss quantities, and produced outputs
- [crystal.md](crystal.md): crystal-layer operating-point logic, scans, `selected_operating_point`, and `active_for_opo`
- [opo.md](opo.md): OPO-layer inputs, use of `active_for_opo`, operating-point model, and generated plots

Use the conceptual docs to understand the pipeline first, then the per-layer docs when working on a specific module.
