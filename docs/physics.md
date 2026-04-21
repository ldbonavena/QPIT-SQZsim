# Physics

This project uses a compact layered model. The focus is on a clear operating-point pipeline rather than a full general quantum-optics treatment.

## Cavity Losses

The cavity layer uses a reflectivity-based resonant loss model.

Primary inputs:

- `reflectivity_input_resonant`
- `reflectivity_output_resonant`
- `alpha_resonant_per_m`
- `parasitic_roundtrip_loss`

From these, the cavity layer derives:

- output coupling transmission
- internal round-trip loss
- `kappa_ext_Hz`
- `kappa_loss_Hz`
- `kappa_total_Hz`

with

- `kappa_total_Hz = kappa_ext_Hz + kappa_loss_Hz`

The escape efficiency is:

- `escape_efficiency = kappa_ext_Hz / kappa_total_Hz`

This is an intracavity/output-coupling quantity. It is distinct from downstream propagation loss or detector efficiency.

## Crystal Physics

The crystal layer models:

- temperature-dependent refractive indices
- quasi-phase matching
- phase-matching scans versus temperature
- polarization-resolved cavity resonance diagnostics
- double-resonance scans
- focused-beam mode matching
- Boyd-Kleinman focusing analysis

Two operating-point ideas are separated:

- phase matching: optimize nonlinear conversion
- double resonance: align the resonant condition for the signal and idler fields

`delta_phi_wrapped_rad` is the signal-idler round-trip phase mismatch reduced to `[-pi, pi]`. Small absolute value means the two fields are close to double resonance.

## OPO Model

The OPO layer is currently a compact degenerate below-threshold model.

It includes:

- cavity loss and escape quantities from the cavity layer
- crystal-derived nonlinear overlap and effective coupling
- a minimal 2x2 quadrature-basis Langevin model
- frequency-domain squeezing and anti-squeezing spectra

It does not include:

- full non-degenerate dynamics
- multimode dynamics
- pump depletion
- a full first-principles threshold derivation

For layer-specific implementation details, see [cavity.md](cavity.md), [crystal.md](crystal.md), and [opo.md](opo.md).
