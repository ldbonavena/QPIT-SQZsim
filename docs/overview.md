# Overview

This documentation is split into two layers:

- conceptual docs for the overall pipeline and interfaces
- per-layer docs for the cavity, crystal, and OPO modules

## Conceptual Docs

- [architecture.md](architecture.md): project structure, layer boundaries, and the cavity -> crystal -> OPO data flow
- [workflow.md](workflow.md): execution order, rerun conditions, and how the staged workflow is used in practice
- [physics.md](physics.md): high-level physical model, including cavity losses, phase matching, double resonance, and the current OPO scope
- [outputs.md](outputs.md): JSON structure and downstream-facing result interfaces

## Per-Layer Docs

- [cavity.md](cavity.md): cavity-layer inputs, supported geometries, exported loss quantities, and produced outputs
- [crystal.md](crystal.md): crystal-layer operating-point logic, scans, `selected_operating_point`, and `active_for_opo`
- [opo.md](opo.md): OPO-layer inputs, use of `active_for_opo`, operating-point model, and generated plots

Use the conceptual docs to understand the pipeline first, then the per-layer docs when working on a specific module.
