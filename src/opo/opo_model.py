"""Minimal OPO model definitions and below-threshold operating-point helpers.

This module holds the structured parameter containers for the degenerate
below-threshold OPO layer. The current implementation keeps the physics light
and focuses on providing a stable data model that can later be extended with
more complete threshold and nonlinear coupling calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from ..common.constants import PI, TWO_PI
except ImportError:
    from common.constants import PI, TWO_PI

CRYSTAL_LENGTH_CONSISTENCY_TOLERANCE_M = 1e-9


@dataclass(frozen=True)
class OPOParameters:
    """User-facing OPO parameters for one workflow run."""

    pump_power_W: float
    threshold_power_W: float
    signal_wavelength_m: float
    pump_wavelength_m: float
    analysis_sideband_Hz: float
    analysis_span_Hz: tuple[float, float]
    n_analysis_points: int
    detection_efficiency: float
    lo_phase_rad: float = 0.0


@dataclass(frozen=True)
class OPOModelResult:
    """Compact collection of derived OPO quantities used downstream.

    ``threshold_power_W`` is kept for backward compatibility and currently
    equals ``baseline_threshold_power_W``.
    """

    pump_parameter: float
    threshold_power_W: float
    baseline_threshold_power_W: float
    effective_threshold_power_W: float
    pump_power_W: float
    d_eff_pm_per_V: float
    crystal_length_m: float
    cavity_crystal_length_m: float
    effective_mode_area_m2: float
    nonlinear_overlap: float
    effective_nonlinear_coupling: float
    cavity_threshold_factor: float
    cavity_kappa_ext_Hz: float
    cavity_kappa_loss_Hz: float
    cavity_kappa_total_Hz: float
    crystal_gain_source: str
    d_eff_source: str
    crystal_operating_point_mode: str
    crystal_active_temperature_K: float
    crystal_gain_factor: float
    below_threshold: bool
    escape_efficiency: float
    cavity_detuning_Hz: float
    signal_wavelength_m: float
    pump_wavelength_m: float
    notes: tuple[str, ...]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_active_crystal_payload(
    crystal_results: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    active_for_opo = _as_dict(crystal_results.get("active_for_opo"))
    if active_for_opo:
        return (
            active_for_opo,
            _as_dict(active_for_opo.get("phase_matching")),
            _as_dict(active_for_opo.get("mode_matching")),
            _as_dict(active_for_opo.get("boyd_kleinman_analysis")),
            _as_dict(active_for_opo.get("polarization_resonance")),
        )

    selected_operating_point = _as_dict(crystal_results.get("selected_operating_point"))
    legacy_active = {
        "operating_point_mode": crystal_results.get("selected_operating_point_mode", "unknown"),
        "temperature_K": selected_operating_point.get("temperature_K"),
        "crystal_length_m": selected_operating_point.get("crystal_length_m"),
    }
    return (
        legacy_active,
        _as_dict(crystal_results.get("selected_operating_phase_matching", crystal_results.get("phase_matching", {}))),
        _as_dict(crystal_results.get("mode_matching")),
        _as_dict(crystal_results.get("boyd_kleinman_analysis")),
        _as_dict(crystal_results.get("polarization_resonance")),
    )


def _validate_crystal_length_consistency(
    cavity_inputs: dict[str, Any],
    active_for_opo: dict[str, Any],
    tolerance_m: float = CRYSTAL_LENGTH_CONSISTENCY_TOLERANCE_M,
) -> tuple[float, float]:
    cavity_crystal_length_raw = cavity_inputs.get("crystal_length_m")
    active_crystal_length_raw = active_for_opo.get("crystal_length_m")

    cavity_crystal_length_m = float(cavity_crystal_length_raw) if cavity_crystal_length_raw is not None else np.nan
    active_crystal_length_m = float(active_crystal_length_raw) if active_crystal_length_raw is not None else np.nan

    if (
        np.isfinite(cavity_crystal_length_m)
        and np.isfinite(active_crystal_length_m)
        and abs(active_crystal_length_m - cavity_crystal_length_m) > float(tolerance_m)
    ):
        raise ValueError(
            "Selected crystal operating point is inconsistent with loaded cavity geometry: "
            f"active crystal length {active_crystal_length_m:.12g} m vs cavity crystal length "
            f"{cavity_crystal_length_m:.12g} m. Rerun cavity_main with the selected crystal length before running OPO."
        )

    return cavity_crystal_length_m, active_crystal_length_m


def build_opo_parameters(config: dict[str, Any]) -> OPOParameters:
    """Build a validated OPO parameter object from a plain configuration mapping."""
    signal_wavelength_m = config.get("wavelength_s_m", config.get("signal_wavelength_m"))
    pump_wavelength_m = config.get("wavelength_p_m", config.get("pump_wavelength_m"))
    if signal_wavelength_m is None:
        raise KeyError("Missing OPO signal wavelength: expected 'wavelength_s_m'.")
    if pump_wavelength_m is None:
        raise KeyError("Missing OPO pump wavelength: expected 'wavelength_p_m'.")

    return OPOParameters(
        pump_power_W=float(config["pump_power_W"]),
        threshold_power_W=float(config["threshold_power_W"]),
        signal_wavelength_m=float(signal_wavelength_m),
        pump_wavelength_m=float(pump_wavelength_m),
        analysis_sideband_Hz=float(config["analysis_sideband_Hz"]),
        analysis_span_Hz=tuple(float(v) for v in config["analysis_span_Hz"]),
        n_analysis_points=int(config["n_analysis_points"]),
        detection_efficiency=float(config["detection_efficiency"]),
        lo_phase_rad=float(config.get("lo_phase_rad", 0.0)),
    )


def derive_opo_quantities(
    parameters: OPOParameters,
    cavity_data: dict[str, Any],
    crystal_data: dict[str, Any],
) -> OPOModelResult:
    """Build a physics-informed below-threshold OPO operating point from cavity/crystal outputs."""
    cavity_results = cavity_data.get("results", {})
    crystal_results = crystal_data.get("results", {})
    active_for_opo, phase_matching, mode_matching, bk_analysis, _polarization_resonance = _resolve_active_crystal_payload(
        crystal_results
    )
    bk_reference = bk_analysis.get("reference", {})
    crystal_inputs = crystal_data.get("inputs", {})
    cavity_inputs = cavity_data.get("inputs", {})
    cavity_crystal_length_m, active_crystal_length_m = _validate_crystal_length_consistency(
        cavity_inputs,
        active_for_opo,
    )
    selected_operating_point_mode = str(
        active_for_opo.get(
            "operating_point_mode",
            crystal_results.get("selected_operating_point_mode", "unknown"),
        )
    )
    selected_operating_point = _as_dict(crystal_results.get("selected_operating_point", {}))
    crystal_active_temperature_raw = active_for_opo.get("temperature_K", selected_operating_point.get("temperature_K"))
    crystal_active_temperature_K = float(crystal_active_temperature_raw) if crystal_active_temperature_raw is not None else np.nan

    if parameters.threshold_power_W <= 0.0:
        raise ValueError("threshold_power_W must be positive")

    baseline_threshold_power_W = float(parameters.threshold_power_W)
    nonlinear_overlap_raw = mode_matching.get("effective_nonlinear_overlap")
    crystal_gain_source = "effective_nonlinear_overlap"
    if nonlinear_overlap_raw is None:
        nonlinear_overlap_raw = bk_reference.get("bk_reference_factor")
        crystal_gain_source = "bk_reference_factor"
    if nonlinear_overlap_raw is None:
        nonlinear_overlap_raw = 1.0
        crystal_gain_source = "fallback_unity"

    nonlinear_overlap = max(float(nonlinear_overlap_raw), 1e-12)
    d_eff_pm_per_V_raw = crystal_inputs.get("d_eff_pm_per_V")
    d_eff_source = "crystal_input_d_eff_pm_per_V"
    if d_eff_pm_per_V_raw is None:
        d_eff_pm_per_V_raw = 1.0
        d_eff_source = "fallback_unity_pm_per_V"
    d_eff_pm_per_V = max(float(d_eff_pm_per_V_raw), 1e-12)

    crystal_length_m_raw = active_for_opo.get("crystal_length_m")
    crystal_length_source = "active_for_opo.crystal_length_m"
    if crystal_length_m_raw is None:
        crystal_length_m_raw = selected_operating_point.get("crystal_length_m")
        crystal_length_source = "selected_operating_point.crystal_length_m"
    if crystal_length_m_raw is None:
        crystal_length_m_raw = crystal_inputs.get("crystal_length_m")
        crystal_length_source = "inputs.crystal_length_m"
    if crystal_length_m_raw is None:
        crystal_length_m_raw = cavity_inputs.get("crystal_length_m", 0.0)
        crystal_length_source = "cavity_inputs.crystal_length_m"
    crystal_length_m = float(crystal_length_m_raw)
    crystal_length_m = max(crystal_length_m, 1e-12)

    waist_crystal_m_raw = mode_matching.get("waist_crystal_m")
    waist_source = "mode_matching.waist_crystal_m"
    if waist_crystal_m_raw is None:
        waist_crystal_m_raw = crystal_inputs.get("beam_waist_crystal_m")
        waist_source = "inputs.beam_waist_crystal_m"
    if waist_crystal_m_raw is None:
        waist_crystal_m_raw = 30e-6
        waist_source = "fallback_30um"
    waist_crystal_m = max(float(waist_crystal_m_raw), 1e-12)
    effective_mode_area_m2 = max(float(PI * waist_crystal_m**2), 1e-24)

    kappa_ext_hz = float(
        cavity_results.get(
            "kappa_ext_Hz",
            float(cavity_results.get("kappa_ext_rad_s", 0.0)) / TWO_PI,
        )
    )
    kappa_loss_hz = float(
        cavity_results.get(
            "kappa_loss_Hz",
            float(cavity_results.get("kappa_loss_rad_s", 0.0)) / TWO_PI,
        )
    )
    kappa_total_hz = float(
        cavity_results.get(
            "kappa_total_Hz",
            kappa_ext_hz + kappa_loss_hz,
        )
    )
    detuning_hz = float(cavity_inputs.get("detuning_Hz", 0.0))
    escape_efficiency = float(cavity_results.get("escape_efficiency", 0.0))
    linewidth_reference_hz = 1e8

    d_eff_m_per_V = d_eff_pm_per_V * 1e-12
    # This remains a compact nonlinear-gain estimate rather than a full
    # first-principles gain coefficient.
    effective_nonlinear_coupling = max(
        d_eff_m_per_V * crystal_length_m * nonlinear_overlap / np.sqrt(effective_mode_area_m2),
        1e-18,
    )
    # This simplified threshold factor now depends explicitly on the physical
    # cavity coupling and internal loss rates rather than a generic loss proxy.
    cavity_threshold_factor = (max(kappa_total_hz, 0.0) / linewidth_reference_hz) ** 2 / max(
        max(kappa_ext_hz, 0.0) / linewidth_reference_hz,
        1e-12,
    )
    cavity_threshold_factor = max(float(cavity_threshold_factor), 1e-12)

    # Normalize the physically motivated coupling estimate to a dimensionless
    # threshold-scaling factor anchored near typical present run conditions.
    nonlinear_coupling_reference_per_V = 5.0e-10
    coupling_scale = max(effective_nonlinear_coupling / nonlinear_coupling_reference_per_V, 1e-12)
    # ``threshold_power_W`` remains the engineering calibration that sets the
    # watt scale, while the cavity-loss and nonlinear-coupling factors apply
    # the current physics-informed correction around that baseline.
    crystal_gain_factor = coupling_scale
    effective_threshold_power_W = (
        baseline_threshold_power_W * (1.0 + cavity_threshold_factor) / coupling_scale
    )
    pump_parameter = float(parameters.pump_power_W) / effective_threshold_power_W

    notes = [
        "Physics-informed OPO operating-point model.",
        "The threshold uses cavity coupling/loss rates together with a crystal-derived nonlinear-coupling estimate.",
        "The nonlinear coupling includes d_eff, crystal length, nonlinear overlap, and effective mode area.",
        "The user-supplied threshold power is retained as a calibration scale, not as the full threshold model.",
        "This remains an intermediate model rather than a full first-principles threshold derivation.",
    ]
    if "pm_power_best" in phase_matching:
        notes.append("Crystal phase-matching output is loaded and available for future coupling calibration.")
    notes.append(f"Crystal gain source: {crystal_gain_source}.")
    notes.append(f"d_eff source: {d_eff_source}.")
    notes.append(f"Crystal operating point mode loaded from crystal workflow: {selected_operating_point_mode}.")
    notes.append(f"Crystal length source: {crystal_length_source}.")
    notes.append(f"Waist source for effective mode area: {waist_source}.")
    notes.append("The nonlinear-overlap term may fall back to the BK reference factor when direct mode-matching data is unavailable.")
    notes.append("Cavity escape efficiency is an intracavity/output-coupling quantity and remains distinct from detection efficiency.")
    notes.append(
        f"Nonlinear coupling reference scale for threshold normalization: {nonlinear_coupling_reference_per_V:.3e} 1/V."
    )

    return OPOModelResult(
        pump_parameter=float(pump_parameter),
        threshold_power_W=baseline_threshold_power_W,
        baseline_threshold_power_W=baseline_threshold_power_W,
        effective_threshold_power_W=float(effective_threshold_power_W),
        pump_power_W=float(parameters.pump_power_W),
        d_eff_pm_per_V=float(d_eff_pm_per_V),
        crystal_length_m=float(crystal_length_m),
        cavity_crystal_length_m=float(cavity_crystal_length_m),
        effective_mode_area_m2=float(effective_mode_area_m2),
        nonlinear_overlap=float(nonlinear_overlap),
        effective_nonlinear_coupling=float(effective_nonlinear_coupling),
        cavity_threshold_factor=float(cavity_threshold_factor),
        cavity_kappa_ext_Hz=float(kappa_ext_hz),
        cavity_kappa_loss_Hz=float(kappa_loss_hz),
        cavity_kappa_total_Hz=float(kappa_total_hz),
        crystal_gain_source=crystal_gain_source,
        d_eff_source=d_eff_source,
        crystal_operating_point_mode=str(selected_operating_point_mode),
        crystal_active_temperature_K=float(crystal_active_temperature_K),
        crystal_gain_factor=float(crystal_gain_factor),
        below_threshold=bool(pump_parameter < 1.0),
        escape_efficiency=escape_efficiency,
        cavity_detuning_Hz=detuning_hz,
        signal_wavelength_m=float(parameters.signal_wavelength_m),
        pump_wavelength_m=float(parameters.pump_wavelength_m),
        notes=tuple(notes),
    )


__all__ = [
    "OPOParameters",
    "OPOModelResult",
    "build_opo_parameters",
    "derive_opo_quantities",
]
