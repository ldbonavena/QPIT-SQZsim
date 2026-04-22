# Cavity Layer

This page documents the cavity-side modules and exported interface.

## Role

The cavity layer defines the resonator geometry and the resonant-field loss model. It is responsible for producing the beam, geometric, and loss quantities used by the crystal and OPO layers.

The entry point is:

- `src/cavity/cavity_main.py`

## What `cavity_main.py` Does

The cavity script:

- selects a geometry
- defines geometry parameters
- defines resonant reflectivities and distributed/parasitic loss inputs
- computes a representative operating point
- computes derived cavity quantities
- writes the cavity JSON output
- writes cavity plots

## Workflow

The cavity layer performs the following steps:

1. Define the geometry and physical parameters
2. Build the round-trip ABCD model
3. Evaluate a cavity operating point (`q`, `m`)
4. Compute the beam waist inside the crystal
5. Build the resonant-field loss model
6. Compute FSR, decay rates, and escape efficiency
7. Export results for downstream layers

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

These inputs are defined in `cavity_main.py` and interpreted in `cavity_workflow.py` and the geometry-specific ABCD builders in `cavity_abcd.py`.

## Resonant Loss Model

The cavity is described using a physically explicit resonant-field loss model.

The main inputs are:

- `R1_resonant`: reflectivity of the non-output mirror or facet
- `R2_resonant`: reflectivity of the output coupler
- `alpha_resonant_per_m`: distributed resonant-field loss coefficient in the crystal
- `L_parasitic_rt`: additional parasitic round-trip loss

From these inputs, the cavity layer derives:

- input and output transmissions
- bulk round-trip loss
- total internal round-trip loss
- decay rates
- escape efficiency

The distributed loss coefficient is applied over the crystal round-trip propagation length.

See [03_physics.md](../03_physics.md) for the physical meaning of the loss model.

## Decay Rates and FSR

The cavity layer computes:

- `FSR`: free spectral range from the optical round-trip length
- `kappa_ext`: decay rate due to output coupling
- `kappa_loss`: decay rate due to internal loss
- `kappa_total = kappa_ext + kappa_loss`

These rates are exported in both:

- angular units (`rad/s`)
- frequency units (`Hz`)

The escape efficiency is defined from the ratio of useful output coupling to total cavity loss.

## Monolithic Geometry

In the monolithic case:

- the cavity is entirely inside the crystal
- the two resonant reflectivities correspond to coated crystal facets
- the crystal length sets both the nonlinear medium length and the cavity propagation length
- distributed loss applies naturally over the crystal round trip

This makes the monolithic case the most direct implementation of the reflectivity-based cavity model.

## Interface to the Crystal Layer

The cavity layer provides the crystal layer with the quantities needed to evaluate nonlinear interaction and operating conditions, including:

- beam waist inside the crystal
- crystal length
- refractive index
- cavity loss quantities
- FSR and decay rates

These define the spatial mode and loss conditions used in the crystal layer.

## Outputs

The cavity JSON output is the crystal-layer input.

Its structure is:

- `inputs`: resolved physical parameters used to define the cavity
- `results`: compact quantities used by downstream layers
- `debug_data`: internal diagnostics such as `q` parameters and `m_factor`

The compact `results` payload includes:

- beam waist in the crystal
- cavity length and optical round-trip length
- FSR
- reflectivities and transmissions
- round-trip loss quantities
- decay rates
- escape efficiency
- Gouy phases

For the JSON layout, see [04_outputs.md](../04_outputs.md).