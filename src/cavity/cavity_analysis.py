"""Cavity physics analysis utilities built on ABCD matrices."""

from __future__ import annotations

import numpy as np
import sympy as sp

from cavity_abcd import CavityAbcdBuilder
from cavity_abcd import Abcd


def cavity_stability(matrix):
    """Return cavity stability m-factor = (A + D) / 2."""
    A, _, _, D = Abcd.parameters(matrix)
    return (A + D) / 2


def cavity_q_parameter(matrix):
    """Return stable cavity q parameter from round-trip ABCD matrix."""
    A, B, C, D = Abcd.parameters(matrix)
    return -1 * (D - A) / (2 * C) + sp.I * sp.sqrt(1 - ((D + A) / 2) ** 2) / sp.Abs(C)


def beam_waist_from_q(q_parameter, wavelength, refractive_index=1):
    """Compute beam waist radius from q parameter imaginary part."""
    q_im = np.imag(q_parameter)
    return np.sqrt(wavelength * q_im / (refractive_index * np.pi))


def optical_roundtrip_length(cavity_length_m, optical_crystal_length_m, n_crystal):
    """Return optical round-trip cavity length in meters."""
    return float(cavity_length_m + (n_crystal - 1.0) * optical_crystal_length_m)


def fsr_from_roundtrip_length(L_optical_m, c_m_per_s):
    """Return free spectral range in Hz from optical round-trip length."""
    return float(c_m_per_s / L_optical_m)


def distributed_roundtrip_loss(alpha_per_m: float, roundtrip_propagation_length_m: float) -> float:
    """Return distributed round-trip power loss from a crystal-medium attenuation coefficient."""
    alpha = max(float(alpha_per_m), 0.0)
    length_m = max(float(roundtrip_propagation_length_m), 0.0)
    return float(1.0 - np.exp(-alpha * length_m))


def resolve_resonant_loss_model(parameters: dict, roundtrip_propagation_length_m: float) -> dict[str, float | str]:
    """Resolve one physically explicit resonant-loss model from new or legacy inputs.

    New convention:
    - ``R1_resonant``: non-output resonant mirror/facet reflectivity
    - ``R2_resonant``: output-coupler reflectivity
    - ``alpha_resonant_per_m``: distributed resonant power-loss coefficient
    - ``L_parasitic_rt``: extra round-trip internal power loss

    Legacy convention:
    - ``f_T_ext``: output coupling transmission
    - ``f_L_rt``: internal round-trip power loss
    """
    uses_new = any(
        key in parameters
        for key in ("R1_resonant", "R2_resonant", "alpha_resonant_per_m", "L_parasitic_rt")
    )
    uses_legacy = any(key in parameters for key in ("f_T_ext", "f_L_rt"))

    if uses_new and uses_legacy:
        raise ValueError(
            "Mixed cavity loss conventions are not allowed. Use either the reflectivity-based "
            "inputs (R1_resonant/R2_resonant/alpha_resonant_per_m/L_parasitic_rt) or the legacy "
            "inputs (f_T_ext/f_L_rt), but not both."
        )

    if uses_new:
        if "R1_resonant" not in parameters or "R2_resonant" not in parameters:
            raise ValueError("Reflectivity-based cavity loss model requires both R1_resonant and R2_resonant.")
        reflectivity_input = float(parameters["R1_resonant"])
        reflectivity_output = float(parameters["R2_resonant"])
        alpha_resonant_per_m = float(parameters.get("alpha_resonant_per_m", 0.0))
        parasitic_roundtrip_loss = float(parameters.get("L_parasitic_rt", 0.0))
        source = "reflectivity_based"
    else:
        output_coupling_transmission = float(parameters.get("f_T_ext", 0.0))
        internal_roundtrip_loss = float(parameters.get("f_L_rt", 0.0))
        reflectivity_input = 1.0
        reflectivity_output = 1.0 - output_coupling_transmission
        alpha_resonant_per_m = 0.0
        parasitic_roundtrip_loss = internal_roundtrip_loss
        source = "legacy_f_T_ext_f_L_rt"

    for label, value in (
        ("R1_resonant", reflectivity_input),
        ("R2_resonant", reflectivity_output),
    ):
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{label} must satisfy 0 <= R <= 1. Received {value}.")
    for label, value in (
        ("alpha_resonant_per_m", alpha_resonant_per_m),
        ("L_parasitic_rt", parasitic_roundtrip_loss),
    ):
        if value < 0.0:
            raise ValueError(f"{label} must be non-negative. Received {value}.")

    input_coupler_transmission = 1.0 - reflectivity_input
    output_coupling_transmission = 1.0 - reflectivity_output
    bulk_roundtrip_loss = distributed_roundtrip_loss(alpha_resonant_per_m, roundtrip_propagation_length_m)
    internal_roundtrip_loss = input_coupler_transmission + bulk_roundtrip_loss + parasitic_roundtrip_loss

    if output_coupling_transmission >= 1.0:
        raise ValueError("Output coupling transmission must be less than 1.")
    if internal_roundtrip_loss >= 1.0:
        raise ValueError(
            "Internal round-trip loss must be less than 1. Check R1_resonant, alpha_resonant_per_m, and L_parasitic_rt."
        )

    return {
        "loss_model_source": source,
        "roundtrip_propagation_length_m": float(roundtrip_propagation_length_m),
        "reflectivity_input_resonant": float(reflectivity_input),
        "reflectivity_output_resonant": float(reflectivity_output),
        "input_coupler_transmission": float(input_coupler_transmission),
        "output_coupling_transmission": float(output_coupling_transmission),
        "alpha_resonant_per_m": float(alpha_resonant_per_m),
        "bulk_roundtrip_loss": float(bulk_roundtrip_loss),
        "parasitic_roundtrip_loss": float(parasitic_roundtrip_loss),
        "internal_roundtrip_loss": float(internal_roundtrip_loss),
    }


def compute_decay_rates(
    L_optical_m: float,
    c_m_per_s: float,
    output_coupling_transmission: float,
    internal_roundtrip_loss: float,
):
    """Compute cavity decay rates.

    ``kappa_*_rad_s`` are angular decay rates in rad/s.
    ``kappa_*_Hz`` are the corresponding cycle-per-second rates.
    """
    roundtrip_frequency_hz = float(c_m_per_s / L_optical_m)
    kappa_ext_hz_like = 0.5 * roundtrip_frequency_hz * float(output_coupling_transmission)
    kappa_loss_hz_like = 0.5 * roundtrip_frequency_hz * float(internal_roundtrip_loss)
    kappa_ext = 2.0 * np.pi * kappa_ext_hz_like
    kappa_loss = 2.0 * np.pi * kappa_loss_hz_like
    kappa_total = kappa_ext + kappa_loss
    return {
        "kappa_ext_rad_s": float(kappa_ext),
        "kappa_ext_Hz": float(kappa_ext_hz_like),
        "kappa_loss_rad_s": float(kappa_loss),
        "kappa_loss_Hz": float(kappa_loss_hz_like),
        "kappa_int_rad_s": float(kappa_loss),
        "kappa_int_Hz": float(kappa_loss_hz_like),
        "kappa_total_rad_s": float(kappa_total),
        "kappa_total_Hz": float(kappa_ext_hz_like + kappa_loss_hz_like),
        "escape_efficiency": float(kappa_ext / kappa_total) if kappa_total != 0 else np.nan,
    }


def gouy_phases_from_m_factor(geometry, m_factor_dict):
    """Return sagittal/tangential Gouy phases in radians from m-factors."""
    psi_sagittal = np.arccos(m_factor_dict["sagittal"])
    if geometry in ("bowtie", "triangle"):
        psi_tangential = np.arccos(m_factor_dict["tangential"])
    else:
        psi_tangential = psi_sagittal
    return {
        "gouy_phase_sagittal_rad": float(psi_sagittal),
        "gouy_phase_tangential_rad": float(psi_tangential),
    }


def bowtie_m_factor(long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index, plane="sagittal"):
    """Return bow-tie cavity m-factor for a selected plane."""
    matrix = CavityAbcdBuilder.bowtie_roundtrip(
        long_axis,
        short_axis,
        crystal_length,
        radius_of_curvature,
        refractive_index,
        incidence_angle,
        plane=plane,
    )
    return cavity_stability(matrix)


def bowtie_q_parameter(long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index, plane="sagittal"):
    """Return bow-tie cavity q parameter for a selected plane."""
    matrix = CavityAbcdBuilder.bowtie_roundtrip(
        long_axis,
        short_axis,
        crystal_length,
        radius_of_curvature,
        refractive_index,
        incidence_angle,
        plane=plane,
    )
    return cavity_q_parameter(matrix)


def linear_m_factor(radius_of_curvature, cavity_length, crystal_length, refractive_index):
    """Return m-factor for a symmetric linear cavity."""
    matrix = CavityAbcdBuilder.linear_roundtrip(
        cavity_length,
        crystal_length,
        radius_of_curvature,
        radius_of_curvature,
        refractive_index,
    )
    return cavity_stability(matrix)


def linear_q_parameter(radius_of_curvature, cavity_length, crystal_length, refractive_index):
    """Return q parameter for a symmetric linear cavity."""
    matrix = CavityAbcdBuilder.linear_roundtrip(
        cavity_length,
        crystal_length,
        radius_of_curvature,
        radius_of_curvature,
        refractive_index,
    )
    return cavity_q_parameter(matrix)


def hemilithic_m_factor(radius_of_curvature, air_gap, crystal_length, refractive_index):
    """Return m-factor for a hemilithic cavity."""
    matrix = CavityAbcdBuilder.hemilithic_roundtrip(
        air_gap,
        crystal_length,
        radius_of_curvature,
        refractive_index,
    )
    return cavity_stability(matrix)


def hemilithic_q_parameter(radius_of_curvature, air_gap, crystal_length, refractive_index):
    """Return q parameter for a hemilithic cavity."""
    matrix = CavityAbcdBuilder.hemilithic_roundtrip(
        air_gap,
        crystal_length,
        radius_of_curvature,
        refractive_index,
    )
    return cavity_q_parameter(matrix)


def monolithic_m_factor(radius_of_curvature, crystal_length, refractive_index):
    """Return m-factor for a monolithic crystal cavity."""
    matrix = CavityAbcdBuilder.monolithic_roundtrip(
        crystal_length,
        refractive_index,
        radius_of_curvature,
    )
    return cavity_stability(matrix)


def monolithic_q_parameter(radius_of_curvature, crystal_length, refractive_index):
    """Return q parameter for a monolithic crystal cavity."""
    matrix = CavityAbcdBuilder.monolithic_roundtrip(
        crystal_length,
        refractive_index,
        radius_of_curvature,
    )
    return cavity_q_parameter(matrix)


def triangle_m_factor(width, height, crystal_length, radius_of_curvature, refractive_index, plane="sagittal"):
    """Return m-factor for a triangular cavity."""
    matrix = CavityAbcdBuilder.triangle_roundtrip(
        width,
        height,
        crystal_length,
        radius_of_curvature,
        refractive_index,
        plane=plane,
    )
    return cavity_stability(matrix)


def triangle_q_parameter(width, height, crystal_length, radius_of_curvature, refractive_index, plane="sagittal"):
    """Return q parameter for a triangular cavity."""
    matrix = CavityAbcdBuilder.triangle_roundtrip(
        width,
        height,
        crystal_length,
        radius_of_curvature,
        refractive_index,
        plane=plane,
    )
    return cavity_q_parameter(matrix)


def make_m_factor_estimator(geometry: str, plane: str = "sagittal"):
    """Build a NumPy-callable m-factor estimator for a geometry."""
    if geometry == "bowtie":
        long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index = sp.symbols(
            "long_axis short_axis incidence_angle crystal_length radius_of_curvature refractive_index", positive=True, real=True
        )
        expr = bowtie_m_factor(
            long_axis,
            short_axis,
            incidence_angle,
            crystal_length,
            radius_of_curvature,
            refractive_index,
            plane=plane,
        )
        return sp.lambdify(
            (long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "linear":
        radius_of_curvature, cavity_length, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature cavity_length crystal_length refractive_index", positive=True, real=True
        )
        expr = linear_m_factor(radius_of_curvature, cavity_length, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, cavity_length, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "hemilithic":
        radius_of_curvature, air_gap, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature air_gap crystal_length refractive_index", positive=True, real=True
        )
        expr = hemilithic_m_factor(radius_of_curvature, air_gap, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, air_gap, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "monolithic":
        radius_of_curvature, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature crystal_length refractive_index", positive=True, real=True
        )
        expr = monolithic_m_factor(radius_of_curvature, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "triangle":
        width, height, crystal_length, radius_of_curvature, refractive_index = sp.symbols(
            "width height crystal_length radius_of_curvature refractive_index", positive=True, real=True
        )
        expr = triangle_m_factor(width, height, crystal_length, radius_of_curvature, refractive_index, plane=plane)
        return sp.lambdify(
            (width, height, crystal_length, radius_of_curvature, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    raise ValueError("geometry must be 'bowtie', 'linear', 'triangle', 'hemilithic', or 'monolithic'")


def make_q_estimator(geometry: str, plane: str = "sagittal"):
    """Build a NumPy-callable q-parameter estimator for a geometry."""
    if geometry == "bowtie":
        long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index = sp.symbols(
            "long_axis short_axis incidence_angle crystal_length radius_of_curvature refractive_index", positive=True, real=True
        )
        expr = bowtie_q_parameter(
            long_axis,
            short_axis,
            incidence_angle,
            crystal_length,
            radius_of_curvature,
            refractive_index,
            plane=plane,
        )
        return sp.lambdify(
            (long_axis, short_axis, incidence_angle, crystal_length, radius_of_curvature, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "linear":
        radius_of_curvature, cavity_length, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature cavity_length crystal_length refractive_index", positive=True, real=True
        )
        expr = linear_q_parameter(radius_of_curvature, cavity_length, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, cavity_length, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "hemilithic":
        radius_of_curvature, air_gap, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature air_gap crystal_length refractive_index", positive=True, real=True
        )
        expr = hemilithic_q_parameter(radius_of_curvature, air_gap, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, air_gap, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "monolithic":
        radius_of_curvature, crystal_length, refractive_index = sp.symbols(
            "radius_of_curvature crystal_length refractive_index", positive=True, real=True
        )
        expr = monolithic_q_parameter(radius_of_curvature, crystal_length, refractive_index)
        return sp.lambdify(
            (radius_of_curvature, crystal_length, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    if geometry == "triangle":
        width, height, crystal_length, radius_of_curvature, refractive_index = sp.symbols(
            "width height crystal_length radius_of_curvature refractive_index", positive=True, real=True
        )
        expr = triangle_q_parameter(width, height, crystal_length, radius_of_curvature, refractive_index, plane=plane)
        return sp.lambdify(
            (width, height, crystal_length, radius_of_curvature, refractive_index),
            expr,
            modules="numpy",
            cse=True,
        )

    raise ValueError("geometry must be 'bowtie', 'linear', 'triangle', 'hemilithic', or 'monolithic'")


__all__ = [
    "cavity_stability",
    "cavity_q_parameter",
    "beam_waist_from_q",
    "optical_roundtrip_length",
    "fsr_from_roundtrip_length",
    "compute_decay_rates",
    "gouy_phases_from_m_factor",
    "bowtie_m_factor",
    "bowtie_q_parameter",
    "linear_m_factor",
    "linear_q_parameter",
    "hemilithic_m_factor",
    "hemilithic_q_parameter",
    "monolithic_m_factor",
    "monolithic_q_parameter",
    "triangle_m_factor",
    "triangle_q_parameter",
    "make_m_factor_estimator",
    "make_q_estimator",
]
