# 00 — Overview

This documentation describes the structure and usage of the QPIT-SQZsim simulator, a pipeline for modeling optical parametric oscillators:

cavity → crystal → OPO

Start from this overview and follow the recommended reading order below.

## Documentation Structure

The documentation is organized into two parts:

- **Conceptual docs**: explain the overall pipeline and interfaces  
- **Module docs**: describe each layer in detail (cavity, crystal, OPO)

Top-level files provide the conceptual view.  
`docs/modules/` contains layer-specific technical documentation.

## Recommended Reading Order

Follow this order to understand the project:

1. Overview — overall structure  
2. Architecture — layer responsibilities  
3. Workflow — how to run the pipeline  
4. Physics — physical model  
5. Outputs — JSON interface  

## Conceptual Docs

- [01_architecture.md](01_architecture.md): project structure, layer boundaries, and the cavity → crystal → OPO data flow  
- [02_workflow.md](02_workflow.md): execution order, rerun conditions, and how the staged workflow is used in practice  
- [03_physics.md](03_physics.md): high-level physical model, including cavity losses, phase matching, double resonance, and the current OPO scope  
- [04_outputs.md](04_outputs.md): JSON structure and downstream-facing result interfaces  

## Module Docs

- [cavity.md](modules/cavity.md): cavity-layer inputs, supported geometries, loss model, and exported quantities  
- [crystal.md](modules/crystal.md): operating-point logic, scans, and `active_for_opo`  
- [opo.md](modules/opo.md): OPO model, use of `active_for_opo`, and generated outputs  

## How to Use These Docs

Start with the conceptual docs to understand the full pipeline.

Then use the module-specific docs when working on a particular layer or modifying the code.