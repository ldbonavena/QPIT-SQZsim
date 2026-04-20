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
    effective_mode_area_m2: float
    # ``nonlinear_coupling_proxy`` is the raw crystal-derived quantity, while
    # ``crystal_gain_factor`` is the threshold-rescaling quantity used by this
    # intermediate operating-point model.
    nonlinear_coupling_proxy: float
    nonlinear_overlap: float
    effective_nonlinear_coupling: float
    cavity_loss_scale: float
    crystal_gain_source: str
    d_eff_source: str
    crystal_gain_factor: float
    below_threshold: bool
    escape_efficiency: float
    cavity_linewidth_Hz: float
    cavity_detuning_Hz: float
    signal_wavelength_m: float
    pump_wavelength_m: float
    notes: tuple[str, ...]


def build_opo_parameters(config: dict[str, Any]) -> OPOParameters:
    """Build a validated OPO parameter object from a plain configuration mapping."""
    return OPOParameters(
        pump_power_W=float(config["pump_power_W"]),
        threshold_power_W=float(config["threshold_power_W"]),
        signal_wavelength_m=float(config["signal_wavelength_m"]),
        pump_wavelength_m=float(config["pump_wavelength_m"]),
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
    phase_matching = crystal_results.get("phase_matching", {})
    mode_matching = crystal_results.get("mode_matching", {})
    bk_analysis = crystal_results.get("boyd_kleinman_analysis", {})
    bk_reference = bk_analysis.get("reference", {})
    crystal_inputs = crystal_data.get("inputs", {})
    cavity_inputs = cavity_data.get("inputs", {})

    if parameters.threshold_power_W <= 0.0:
        raise ValueError("threshold_power_W must be positive")

    baseline_threshold_power_W = float(parameters.threshold_power_W)
    nonlinear_coupling_proxy_raw = mode_matching.get("effective_nonlinear_overlap")
    crystal_gain_source = "effective_nonlinear_overlap"
    if nonlinear_coupling_proxy_raw is None:
        nonlinear_coupling_proxy_raw = bk_reference.get("bk_reference_factor")
        crystal_gain_source = "bk_reference_factor"
    if nonlinear_coupling_proxy_raw is None:
        nonlinear_coupling_proxy_raw = 1.0
        crystal_gain_source = "fallback_unity"

    nonlinear_coupling_proxy = max(float(nonlinear_coupling_proxy_raw), 1e-12)
    # In the current intermediate model, ``nonlinear_overlap`` stores the
    # overlap-like crystal coupling factor used by the OPO layer, even when it
    # comes from fallback proxy sources such as the BK reference factor.
    nonlinear_overlap = nonlinear_coupling_proxy
    d_eff_pm_per_V_raw = crystal_inputs.get("d_eff_pm_per_V")
    d_eff_source = "crystal_input_d_eff_pm_per_V"
    if d_eff_pm_per_V_raw is None:
        d_eff_pm_per_V_raw = 1.0
        d_eff_source = "fallback_unity_pm_per_V"
    d_eff_pm_per_V = max(float(d_eff_pm_per_V_raw), 1e-12)

    crystal_length_m = float(
        crystal_inputs.get(
            "crystal_length_m",
            cavity_inputs.get("crystal_length_m", 0.0),
        )
    )
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
    effective_mode_area_m2 = max(float(np.pi * waist_crystal_m**2), 1e-24)

    linewidth_hz = float(cavity_results.get("kappa_total_Hz", 0.0))
    detuning_hz = float(cavity_inputs.get("detuning_Hz", 0.0))
    escape_efficiency = float(cavity_results.get("escape_efficiency", 0.0))
    linewidth_reference_hz = 1e8

    d_eff_m_per_V = d_eff_pm_per_V * 1e-12
    # This remains a compact proxy for nonlinear gain rather than a full
    # first-principles gain coefficient.
    effective_nonlinear_coupling = max(
        d_eff_m_per_V * crystal_length_m * nonlinear_overlap / np.sqrt(effective_mode_area_m2),
        1e-18,
    )
    # Higher cavity loss raises the threshold proxy; lower escape efficiency
    # weakly penalizes the estimate in this intermediate model.
    cavity_loss_scale = (max(linewidth_hz, 0.0) / linewidth_reference_hz) ** 2 / max(
        np.sqrt(max(escape_efficiency, 0.0)),
        1e-12,
    )
    cavity_loss_scale = max(float(cavity_loss_scale), 1e-12)

    # Normalize the physically motivated coupling proxy to a dimensionless
    # threshold-scaling factor anchored near typical present run conditions.
    nonlinear_coupling_reference_per_V = 5.0e-10
    coupling_scale = max(effective_nonlinear_coupling / nonlinear_coupling_reference_per_V, 1e-12)
    # ``threshold_power_W`` remains the engineering calibration that sets the
    # watt scale, while the cavity-loss and nonlinear-coupling proxies apply
    # the current physics-informed correction around that baseline.
    crystal_gain_factor = coupling_scale
    effective_threshold_power_W = (
        baseline_threshold_power_W * (1.0 + cavity_loss_scale) / coupling_scale
    )
    pump_parameter = float(parameters.pump_power_W) / effective_threshold_power_W

    notes = [
        "Physics-informed OPO operating-point model.",
        "The threshold uses a cavity-loss proxy together with a crystal-derived nonlinear-coupling estimate.",
        "The nonlinear coupling includes d_eff, crystal length, nonlinear overlap, and effective mode area.",
        "The user-supplied threshold power is retained as a calibration scale, not as the full threshold model.",
        "This remains an intermediate model rather than a full first-principles threshold derivation.",
    ]
    if "pm_power_best" in phase_matching:
        notes.append("Crystal phase-matching output is loaded and available for future coupling calibration.")
    notes.append(f"Crystal gain source: {crystal_gain_source}.")
    notes.append(f"d_eff source: {d_eff_source}.")
    notes.append(f"Waist source for effective mode area: {waist_source}.")
    notes.append("The nonlinear-overlap term may come from fallback proxy sources when direct mode-matching data is unavailable.")
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
        effective_mode_area_m2=float(effective_mode_area_m2),
        nonlinear_coupling_proxy=float(nonlinear_coupling_proxy),
        nonlinear_overlap=float(nonlinear_overlap),
        effective_nonlinear_coupling=float(effective_nonlinear_coupling),
        cavity_loss_scale=float(cavity_loss_scale),
        crystal_gain_source=crystal_gain_source,
        d_eff_source=d_eff_source,
        crystal_gain_factor=float(crystal_gain_factor),
        below_threshold=bool(pump_parameter < 1.0),
        escape_efficiency=escape_efficiency,
        cavity_linewidth_Hz=linewidth_hz,
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
