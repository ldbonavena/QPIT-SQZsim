# Cavity Layer

This page documents the cavity-side modules and exported interface.

## Role

The cavity layer defines the resonator geometry and the resonant-field loss model. It is responsible for producing the beam and loss quantities used by the crystal and OPO layers.

The entry point is:

- `src/cavity/cavity_main.py`

## What `cavity_main.py` Does

The cavity script:

- selects a geometry
- defines geometry parameters
- defines resonant reflectivities and distributed/parasitic loss inputs
- computes the single operating point
- computes derived cavity quantities
- writes the cavity JSON
- writes cavity plots

## Supported Geometries

The current code supports:

- `bowtie`
- `linear`
- `triangle`
- `hemilithic`
- `monolithic`

For `monolithic`, the resonant reflectivities correspond naturally to the two coated crystal facets.

## Geometry Inputs

The exact geometry inputs depend on the selected geometry, but they include quantities such as:

- crystal length
- crystal refractive index
- mirror or facet radius of curvature
- cavity lengths, gaps, widths, or heights depending on geometry

These inputs are defined in `cavity_main.py` and interpreted in `cavity_workflow.py` and the geometry-specific ABCD helpers.

## Exported Loss Quantities

The cavity layer exports:

- `reflectivity_input_resonant`
- `reflectivity_output_resonant`
- `alpha_resonant_per_m`
- `parasitic_roundtrip_loss`
- `output_coupling_transmission`
- `internal_roundtrip_loss`
- `kappa_ext_Hz`
- `kappa_loss_Hz`
- `kappa_total_Hz`
- `escape_efficiency`

See [03_physics.md](03_physics.md) for the physical meaning of these loss quantities.

## Outputs

The cavity JSON is the crystal-layer input.

Its compact `results` payload includes:

- beam waist in the crystal
- cavity length and optical round-trip length
- FSR
- loss and coupling quantities
- Gouy phases

Heavy internal details such as `q` parameters and `m_factor` are kept in `debug_data`.

For the JSON layout, see [04_outputs.md](04_outputs.md).
