# 04 — Outputs

The simulator writes one JSON output per layer. The current structure is:

```json
{
  "inputs": { ... },
  "results": { ... },
  "debug_data": { ... }
}
```

`debug_data` is optional.

## Inputs

`inputs` contains the information needed to understand how the file was produced.

Typical contents:

- geometry
- upstream JSON paths
- wavelengths
- crystal length
- cavity reflectivities and loss inputs
- configured operating-point mode

## Results

`results` contains the compact downstream-facing payload.

Examples:

- cavity: beam waist, FSR, `kappa_*`, `escape_efficiency`
- crystal: selected operating point, compact mode matching, compact BK summary, active polarization resonance, `active_for_opo`
- OPO: operating-point model and squeezing spectrum

## Debug Data

`debug_data` contains heavy or diagnostic payloads that are not needed downstream.

Typical contents:

- phase-matching scans
- double-resonance scans
- full Boyd-Kleinman maps
- Langevin matrices

The intention is:

- `results` stays minimal
- `debug_data` carries large arrays and diagnostic details

## `active_for_opo`

`crystal.results.active_for_opo` is the resolved crystal-side handoff to OPO.

It contains:

- `operating_point_mode`
- `temperature_K`
- `crystal_length_m`
- `phase_matching`
- `mode_matching`
- `boyd_kleinman_analysis`
- `polarization_resonance`

This block is the selected crystal operating point as consumed by OPO.

For the technical meaning of the layer-specific fields, see [cavity.md](cavity.md), [crystal.md](crystal.md), and [opo.md](opo.md).
