# QPIT-SQZsim

A modular simulation framework for optical parametric oscillators (OPOs) and squeezed light generation, combining cavity geometry, crystal design physics, and nonlinear interaction modeling.

The project is structured in layers:

cavity → crystal → OPO → squeezing

---

# Project Structure

```
QPIT-SQZsim/
    docs/           # Project documentation
        overview.md
        architecture.md
        cavity.md
        crystal.md
        opo.md
    results/        # local simulation outputs; not intended for version control
    src/
        cavity/     # Cavity geometry and optical mode analysis
            cavity_main.py
            cavity_workflow.py
            cavity_abcd.py
            cavity_analysis.py
            cavity_plotter.py
            optics_abcd.py

        crystal/    # Crystal physics and nonlinear interaction modeling
            crystal_main.py
            crystal_workflow.py
            crystal_materials.py
            crystal_phase_matching.py
            crystal_mode_matching.py
            crystal_boyd_kleinman.py
            crystal_plotter.py

        common/     # Shared utilities (constants, helpers)
            __init__.py
            constants.py
            results_paths.py
        opo/        # Below-threshold degenerate OPO modeling and squeezing workflow
            __init__.py
            opo_main.py
            opo_workflow.py
            opo_model.py
            opo_langevin.py
            opo_squeezing.py
            opo_plotter.py

    LICENSE
    README.md
    requirements.txt
```

The project is structured so that each module has a clear responsibility:

- **cavity/**: geometry definition, ABCD matrices, stability analysis, beam modes
- **crystal/**: crystal design and analysis workflow including dispersion, phase matching, derived QPM poling, mode matching, and focused‑beam nonlinear interaction (Boyd–Kleinman theory)
- **opo/**: below-threshold degenerate OPO modeling, Langevin quadrature response, and squeezing spectra
- **common/**: reusable constants and shared helpers such as results-path management

---

# What the cavity simulation computes

For a given geometry the code computes:

- Stability maps (|m| < 1)
- Eigenmodes via the round-trip ABCD matrix
- Beam waist maps
- Single-point evaluation:
  - q-parameters
  - waist in the crystal
  - round-trip lengths (geometric and optical)

Derived quantities:

- Free Spectral Range (FSR)
- decay rates: `kappa_ext`, `kappa_loss`, `kappa_total`
- escape efficiency and detuning
- Gouy phases

These quantities are the required inputs for later simulations of:

- nonlinear gain
- OPO threshold
- squeezing spectra

---

# Output files

All simulation outputs are written to the local `results/` directory.  
The directory structure is created automatically when simulations are executed.

```
results/
    <geometry>/
        cavity/
            cavity_simulation_output.json
            stability_map.png
            waist_map.png
        crystal/
            crystal_simulation_output.json
            boyd_kleinman_master_map.png
            qpm_length_poling_map.png
            boyd_kleinman_analysis.png
        opo/
            opo_simulation_output.json
            opo_squeezing_spectrum.png
```

Each run produces:

**cavity_simulation_output.json**

Contains all relevant simulation inputs and computed parameters, including:

- cavity geometry parameters
- q‑parameters
- waist sizes
- FSR
- decay rates
- escape efficiency
- Gouy phases

This JSON file is used by the next simulation layer (crystal or OPO).

**stability_map.png**

Visualization of cavity stability across the scanned parameter space.

**waist_map.png**

Beam waist map corresponding to the same parameter scan.

**crystal_simulation_output.json**

Contains the crystal-layer inputs derived from the cavity simulation together with:

- phase-matching scan results
- mode-matching summary values
- Boyd-Kleinman analysis payload
- cavity output reference used to build the crystal context

The crystal results directory now also includes:

- `boyd_kleinman_master_map.png`: universal `h_BK(\sigma,\xi)` map with the system reference operating point and the theoretical master-map optimum
- `qpm_length_poling_map.png`: normalized QPM / poling-length map with first-order QPM guide
- `boyd_kleinman_analysis.png`: system-specific BK sweep analysis around the current operating point

**opo_simulation_output.json**

Contains the OPO-layer inputs and derived operating-point / spectrum quantities, including:

- calibration threshold power
- crystal-resolved nonlinear coupling inputs and sources
- effective threshold power
- pump parameter sigma
- cavity linewidth, escape efficiency, and detuning
- quadrature squeezing results
- measured homodyne spectrum and optimal squeezing phase

**opo_squeezing_spectrum.png**

Frequency-domain OPO noise spectrum in dB, including:

- inferred squeezing
- inferred anti-squeezing
- measured quadrature for the selected LO phase
- shot-noise reference

---

# Modeling approach

The cavity model uses the **ABCD matrix formalism** for paraxial Gaussian beams.

In the crystal section, propagation is modeled using decoupled ABCD elements instead of a single dielectric slab matrix:

- free‑space propagation
- dielectric interfaces
- crystal propagation

In this convention, propagation in free space and in a uniform refractive index medium use the **same propagation matrix**.  
The refractive index enters through the dielectric interface matrices and through the waist calculation.

This modular construction makes it straightforward to extend the simulation with:

- thermal lensing
- curved interfaces
- nonlinear effects

---

## Installation

```bash
git clone <repository-url> QPIT-SQZsim
cd QPIT-SQZsim
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

# Running simulations

Simulations are executed per module (no global pipeline yet).

Run the simulation layers directly from their main entry points:

- `src/cavity/cavity_main.py`
- `src/crystal/crystal_main.py`
- `src/opo/opo_main.py`

Typical usage:

```bash
python -m src.cavity.cavity_main
python -m src.crystal.crystal_main
python -m src.opo.opo_main
```

Both scripts are designed to be run interactively in VS Code using `# %%` cells or as plain Python entry points.

The cavity script generates geometry-dependent cavity results under `results/<geometry>/cavity/`.  
The crystal script loads the cavity output from `results/<geometry>/cavity/cavity_simulation_output.json` and writes crystal results under `results/<geometry>/crystal/`.

## Crystal Workflow

The crystal layer is now organized as a design-oriented OPO workflow.

In the default `design` mode, the user specifies the target wavelengths, crystal model, and a design temperature. The code then derives the required QPM poling period from the bulk phase-matching condition and uses that derived period for the downstream phase-matching scan, mode matching, and BK analysis.

An `analysis` mode is also available when you want to study a chosen crystal configuration directly using an explicit poling period.

The crystal simulation also supports an explicit nonlinear interaction-type selection through `PHASE_MATCHING_TYPE` in `src/crystal/crystal_main.py`. The currently supported choices are `type_0`, `type_I`, and `type_II`. The corresponding pump/signal/idler axis assignment is resolved internally by `src/crystal/crystal_materials.py`.

The high-level crystal execution order is:

1. Load cavity context from `results/<geometry>/cavity/`
2. Derive the design poling period from wavelengths and design temperature, or use the configured analysis period
3. Scan phase matching versus temperature
4. Determine the operating temperature from the phase-matching optimum
5. Evaluate the crystal refractive index at that operating temperature
6. Compute mode matching
7. Run Boyd-Kleinman analysis
8. Build structured result and JSON output
9. Print a summary
10. Generate plots
11. Save outputs

The crystal plotting outputs are:

- BK master map
- QPM / poling-length map
- BK sweep analysis plot

The wavelength sweeps in the BK analysis use fixed pump wavelength and derive the idler from exact three-wave energy conservation.

Shared utilities used by both layers live in:

- `src/common/constants.py`
- `src/common/results_paths.py`

## OPO Workflow

The OPO layer consumes the exported cavity and crystal results and builds a compact below-threshold degenerate OPO model. It uses those upstream results to define a physics-informed operating point, constructs a linearized quadrature Langevin model in the `X/P` basis, and produces frequency-domain squeezing spectra.

The OPO model uses a physics-informed nonlinear coupling derived from the crystal effective nonlinearity (`d_eff`), crystal length, mode overlap, and effective mode area.

Current OPO capabilities include:

- crystal-informed nonlinear coupling using `d_eff`, overlap, and mode size
- physics-informed threshold modeling using cavity loss and crystal nonlinear coupling
- a below-threshold degenerate OPO model
- a 2x2 quadrature Langevin model in the `X/P` basis
- frequency-dependent squeezing and anti-squeezing spectra
- homodyne measurement with configurable LO phase via `lo_phase_rad`
- computation of squeezing, anti-squeezing, measured quadrature spectrum, and optimal squeezing phase

The current implementation is a compact, below-threshold degenerate OPO model intended for rapid exploration and integration with cavity/crystal simulations. It is not yet a full first-principles quantum input-output treatment.

---

# Design principles

- Modular separation of physics layers (cavity → crystal → OPO)
- Explicit data flow via JSON outputs
- Interactive workflow using `# %%` cells
- Minimal dependencies and transparent numerical implementation

---

# Future extensions

Planned developments include:

- additional crystal-model refinements and validation
- further refinement of OPO threshold modeling toward first-principles formulations
- improved quantum input-output and noise modeling
- quantum noise and detection modeling

The modular structure of the repository is designed so that each layer (cavity → crystal → OPO) builds directly on the results exported by the previous stage.

---

## Documentation

Detailed documentation is available in the `docs/` folder:

- architecture overview
- cavity theory and outputs
- crystal modeling
- OPO modeling and squeezing spectra

---

# License

See the `LICENSE` file for details.
