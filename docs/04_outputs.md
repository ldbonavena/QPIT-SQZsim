# 04 — Outputs

This section describes the JSON outputs produced by each layer of the simulator.

These files define the **interface between layers** and are the primary way data flows through the pipeline:

cavity → crystal → OPO

Each stage writes a JSON file that is consumed by the next one.

---

## General Structure

Each JSON file has the form:

```json
{
  "inputs": { ... },
  "results": { ... },
  "debug_data": { ... }
}
```

`debug_data` is optional.

---

## Inputs

`inputs` contains the information needed to understand how the file was produced.

It provides **traceability and reproducibility**.

Typical contents:

- geometry and configuration parameters
- upstream JSON paths
- wavelengths and material choices
- crystal length
- cavity reflectivities and loss inputs
- selected operating-point mode

This block is not used directly downstream, but is essential for debugging and validation.

---

## Results

`results` contains the **compact downstream-facing payload**.

This is the only part that should be used by subsequent layers.

Design principles:

- minimal
- stable
- sufficient to reproduce downstream calculations

Examples:

- **cavity**
  - beam waist
  - optical round-trip length
  - FSR
  - `kappa_ext`, `kappa_loss`, `kappa_total`
  - `escape_efficiency`

- **crystal**
  - selected operating point
  - compact phase matching
  - compact mode matching
  - Boyd–Kleinman summary
  - polarization resonance
  - `active_for_opo`

- **OPO**
  - operating-point model
  - squeezing spectrum

---

## Debug Data

`debug_data` contains heavy or diagnostic payloads that are not needed downstream.

Typical contents:

- phase-matching scans
- double-resonance scans
- full Boyd–Kleinman maps
- Langevin matrices
- intermediate diagnostic quantities

Design principles:

- may be large
- may change structure
- not guaranteed to be stable
- not intended for downstream use

---

## `active_for_opo`

`crystal.results.active_for_opo` is the **core interface between the crystal and OPO layers**.

It represents the **fully resolved crystal operating point**.

It contains:

- `operating_point_mode`
- `temperature_K`
- `crystal_length_m`
- `phase_matching`
- `mode_matching`
- `boyd_kleinman_analysis`
- `polarization_resonance`

This block is:

- the single source of truth for the crystal state
- the only crystal payload used by the OPO layer

The OPO layer must consume this block directly without reinterpretation.

---

## Design Philosophy

The output structure enforces a strict separation:

- `inputs` → how the result was produced  
- `results` → what is needed downstream  
- `debug_data` → optional diagnostics  

This ensures:

- clear interfaces between layers  
- minimal data duplication  
- stable downstream behavior  

---

For the meaning of individual fields, see:

- [cavity.md](modules/cavity.md)
- [crystal.md](modules/crystal.md)
- [opo.md](modules/opo.md)
