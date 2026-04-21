"""High-level workflow assembly for crystal and mode-matching simulations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

try:
    from common.results_paths import ensure_geometry_results_subdirs, get_cavity_results_dir, get_crystal_results_dir
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from common.results_paths import ensure_geometry_results_subdirs, get_cavity_results_dir, get_crystal_results_dir

from .crystal_mode_matching import (
    ModeMatchingResult,
    build_mode_matching_context_from_cavity_output,
    estimate_mode_matching_quantities,
)
from .crystal_boyd_kleinman import (
    BKAnalysisConfig,
    bk_analysis_result_to_dict,
    run_bk_analysis_pair,
)
from .crystal_phase_matching import compute_design_poling_period as compute_design_poling_period_from_material_model
from .crystal_phase_matching import scan_phase_matching_vs_temperature

_BK_MAP_KEYS = frozenset(
    {
        "bk_master_sigma_values",
        "bk_master_xi_values",
        "bk_master_h_map",
    }
)
_CRYSTAL_LENGTH_MATCH_TOLERANCE_M = 1e-9


@dataclass(frozen=True)
class CrystalContext:
    """Structured context loaded from cavity simulation outputs."""

    geometry: str | None
    cavity_output_path: str
    crystal_length_m: float
    wavelength_m: float
    n_crystal: float
    beam_waist_crystal_m: float
    cavity_data: dict[str, Any]


@dataclass(frozen=True)
class CrystalSimulationResult:
    """Combined crystal workflow output."""

    context: CrystalContext
    phase_matching: dict[str, Any]
    mode_matching: ModeMatchingResult
    selected_operating_phase_matching: dict[str, Any] | None = None
    phase_matching_operating_point: dict[str, Any] | None = None
    double_resonance_operating_point: dict[str, Any] | None = None
    selected_operating_point_mode: str | None = None
    selected_operating_point: dict[str, Any] | None = None
    polarization_resonance: dict[str, Any] | None = None
    active_polarization_resonance: dict[str, Any] | None = None
    double_resonance_scan: dict[str, Any] | None = None
    bk_analysis: dict[str, Any] | None = None


def _load_cavity_output_data(path: str | Path) -> dict[str, Any]:
    cavity_output_path = Path(path)
    if not cavity_output_path.exists():
        raise FileNotFoundError(f"Cavity simulation output not found: {cavity_output_path}")
    with cavity_output_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_cavity_context_for_crystal(
    geometry: str,
    cavity_output_path: str | Path | None = None,
) -> CrystalContext:
    """Load cavity JSON output and build the crystal workflow context."""
    if cavity_output_path is None:
        cavity_output_path = get_cavity_results_dir(geometry) / "cavity_simulation_output.json"
    cavity_data = _load_cavity_output_data(cavity_output_path)

    inputs = cavity_data.get("inputs", {})
    results = cavity_data.get("results", {})
    waist_um = results.get("beam_waist_crystal_um")

    if waist_um is None:
        raise ValueError("Cavity output missing results.beam_waist_crystal_um")

    return CrystalContext(
        geometry=str(cavity_data.get("geometry", inputs.get("geometry", geometry))),
        cavity_output_path=str(Path(cavity_output_path)),
        crystal_length_m=float(inputs["crystal_length_m"]),
        wavelength_m=float(inputs["wavelength_m"]),
        n_crystal=float(inputs["n_crystal"]),
        beam_waist_crystal_m=float(waist_um) * 1e-6,
        cavity_data=cavity_data,
    )


def _phase_matching_scan_to_output(scan: dict[str, Any]) -> dict[str, Any]:
    return {key: (value.tolist() if isinstance(value, np.ndarray) else value) for key, value in scan.items()}


def _to_json_compatible(value: Any) -> Any:
    """Recursively convert NumPy-heavy workflow payloads into JSON-safe types."""
    if isinstance(value, dict):
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        items = [_to_json_compatible(item) for item in value]
        if len(items) == 1 and isinstance(items[0], (bool, int, float)) and not isinstance(items[0], str):
            return items[0]
        return items
    if isinstance(value, np.ndarray):
        if value.ndim == 0 or value.size == 1:
            return _to_json_compatible(value.reshape(-1)[0].item())
        return _to_json_compatible(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def compute_crystal_phase_matching(
    context: CrystalContext,
    n_p_of_T: Callable[[float], float],
    n_s_of_T: Callable[[float], float],
    n_i_of_T: Callable[[float], float],
    wavelength_p_m: float,
    wavelength_s_m: float,
    wavelength_i_m: float,
    Lambda0_m: float,
    T_min_K: float,
    T_max_K: float,
    n_T: int,
    T0_K: float = 293.15,
    alpha_perK: float = 0.0,
    qpm_order_m: int = 1,
) -> dict[str, Any]:
    """Compute the phase-matching temperature scan from the cavity-derived context."""
    scan = scan_phase_matching_vs_temperature(
        T_min_K,
        T_max_K,
        n_T,
        wavelength_p_m,
        wavelength_s_m,
        wavelength_i_m,
        n_p_of_T,
        n_s_of_T,
        n_i_of_T,
        Lambda0_m,
        context.crystal_length_m,
        T0_K=T0_K,
        alpha_perK=alpha_perK,
        qpm_order_m=qpm_order_m,
    )
    return _phase_matching_scan_to_output(scan)


def compute_design_poling_period(
    wavelength_p_m: float,
    wavelength_s_m: float,
    wavelength_i_m: float,
    temperature_K: float,
    n_p_of_lambda_T: Callable[[float, float], float],
    n_s_of_lambda_T: Callable[[float, float], float],
    n_i_of_lambda_T: Callable[[float, float], float],
    qpm_order_m: int = 1,
) -> Any:
    """Compute the design poling period from wavelengths and one design temperature."""
    return compute_design_poling_period_from_material_model(
        wavelength_p_m=wavelength_p_m,
        wavelength_s_m=wavelength_s_m,
        wavelength_i_m=wavelength_i_m,
        temperature_K=temperature_K,
        n_p_of_lambda_T=n_p_of_lambda_T,
        n_s_of_lambda_T=n_s_of_lambda_T,
        n_i_of_lambda_T=n_i_of_lambda_T,
        qpm_order_m=qpm_order_m,
    )


def compute_crystal_mode_matching(
    context: CrystalContext,
    n_crystal: float | None = None,
    delta_k_rad_per_m: float = 0.0,
) -> ModeMatchingResult:
    """Compute focusing and mode-matching quantities from the cavity-derived beam parameters."""
    cavity_mode_matching_context = build_mode_matching_context_from_cavity_output(context.cavity_data)
    waist_crystal_m = cavity_mode_matching_context.waist_crystal_m or context.beam_waist_crystal_m
    medium_index = context.n_crystal if n_crystal is None else float(n_crystal)
    return estimate_mode_matching_quantities(
        waist_crystal_m=float(waist_crystal_m),
        crystal_length_m=context.crystal_length_m,
        wavelength_m=context.wavelength_m,
        n_crystal=medium_index,
        delta_k_rad_per_m=delta_k_rad_per_m,
    )


def compute_boyd_kleinman_analysis(
    context: CrystalContext,
    mode_matching: ModeMatchingResult,
    n_p_of_T: Callable[[float], float],
    n_s_of_T: Callable[[float], float],
    n_i_of_T: Callable[[float], float],
    n_p_of_lambda_T: Callable[[float, float], float],
    n_s_of_lambda_T: Callable[[float, float], float],
    n_i_of_lambda_T: Callable[[float, float], float],
    wavelength_p_m: float,
    wavelength_s_m: float,
    wavelength_i_m: float,
    Lambda0_m: float,
    n_T: int,
    T0_K: float = 293.15,
    alpha_perK: float = 0.0,
    qpm_order_m: int = 1,
    phase_matching: dict[str, Any] | None = None,
    bk_config: BKAnalysisConfig | None = None,
) -> dict[str, Any]:
    """Orchestrate BK analysis and expose the plotting-compatible dictionary payload.

    The workflow layer delegates all BK-specific reference construction,
    sweeps, normalization, defaults, and metadata assembly to
    ``crystal_boyd_kleinman``.
    """
    bk_results = run_bk_analysis_pair(
        context=context,
        mode_matching=mode_matching,
        n_p_of_T=n_p_of_T,
        n_s_of_T=n_s_of_T,
        n_i_of_T=n_i_of_T,
        n_p_of_lambda_T=n_p_of_lambda_T,
        n_s_of_lambda_T=n_s_of_lambda_T,
        n_i_of_lambda_T=n_i_of_lambda_T,
        wavelength_p_m=wavelength_p_m,
        wavelength_s_m=wavelength_s_m,
        wavelength_i_m=wavelength_i_m,
        Lambda0_m=Lambda0_m,
        T0_K=T0_K,
        alpha_perK=alpha_perK,
        qpm_order_m=qpm_order_m,
        phase_matching=phase_matching,
        n_temperature=n_T,
        bk_config=bk_config,
    )
    bk_operating = bk_analysis_result_to_dict(bk_results["bk_analysis_operating"])
    bk_optimal = bk_analysis_result_to_dict(bk_results["bk_analysis_optimal"])
    return {
        "reference": bk_operating.get("reference", {}),
        "bk_master_sigma_opt": bk_operating.get("bk_master_sigma_opt"),
        "bk_master_xi_opt": bk_operating.get("bk_master_xi_opt"),
        "bk_master_h_opt": bk_operating.get("bk_master_h_opt"),
        "bk_analysis_operating": bk_operating,
        "bk_analysis_optimal": bk_optimal,
    }


def build_crystal_simulation_result(
    context: CrystalContext,
    phase_matching: dict[str, Any],
    mode_matching: ModeMatchingResult,
    selected_operating_phase_matching: dict[str, Any] | None = None,
    phase_matching_operating_point: dict[str, Any] | None = None,
    double_resonance_operating_point: dict[str, Any] | None = None,
    selected_operating_point_mode: str | None = None,
    selected_operating_point: dict[str, Any] | None = None,
    polarization_resonance: dict[str, Any] | None = None,
    active_polarization_resonance: dict[str, Any] | None = None,
    double_resonance_scan: dict[str, Any] | None = None,
    bk_analysis: dict[str, Any] | None = None,
) -> CrystalSimulationResult:
    """Build the structured crystal workflow result."""
    return CrystalSimulationResult(
        context=context,
        phase_matching=phase_matching,
        mode_matching=mode_matching,
        selected_operating_phase_matching=selected_operating_phase_matching,
        phase_matching_operating_point=phase_matching_operating_point,
        double_resonance_operating_point=double_resonance_operating_point,
        selected_operating_point_mode=selected_operating_point_mode,
        selected_operating_point=selected_operating_point,
        polarization_resonance=polarization_resonance,
        active_polarization_resonance=active_polarization_resonance,
        double_resonance_scan=double_resonance_scan,
        bk_analysis=bk_analysis,
    )


def build_phase_matching_operating_point(
    phase_matching: dict[str, Any],
    resonance_diagnostic: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build the phase-matching operating point candidate."""
    resonance = resonance_diagnostic
    if resonance is None:
        return None

    return {
        "temperature_K": float(phase_matching["T_best_K"][0]),
        "phase_matching_power_factor": float(phase_matching["pm_power_best"][0]),
        "signal_axis": resonance["signal_axis"],
        "idler_axis": resonance["idler_axis"],
        "n_signal": float(resonance["n_signal"]),
        "n_idler": float(resonance["n_idler"]),
        "wrapped_phase_mismatch_rad": float(resonance["delta_phi_wrapped_rad"]),
        "is_double_resonant": bool(resonance["is_double_resonant"]),
    }


def build_double_resonance_operating_point(double_resonance_scan: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build the double-resonance operating point candidate."""
    scan = double_resonance_scan
    if scan is None:
        return None

    return {
        "temperature_K": float(scan["best_temperature_K"]),
        "crystal_length_m": float(scan["best_crystal_length_m"]),
        "wrapped_phase_mismatch_rad": float(scan["best_delta_phi_wrapped_rad"]),
        "abs_wrapped_phase_mismatch_rad": float(scan["best_abs_delta_phi_wrapped_rad"]),
        "is_double_resonant": bool(scan["best_is_double_resonant"]),
    }


def select_crystal_operating_point(
    mode: str,
    phase_matching_operating_point: dict[str, Any] | None,
    double_resonance_operating_point: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the active crystal operating point for one explicit selection mode."""
    normalized_mode = str(mode).strip().lower()
    candidates = {
        "phase_matching": phase_matching_operating_point,
        "double_resonance": double_resonance_operating_point,
    }
    if normalized_mode not in candidates:
        supported = ", ".join(candidates)
        raise ValueError(f"Unknown OPERATING_POINT_MODE: {mode}. Supported values: {supported}")

    selected_operating_point = candidates[normalized_mode]
    if selected_operating_point is None:
        raise ValueError(
            f"Requested operating-point mode '{normalized_mode}' is unavailable for this run."
        )
    return selected_operating_point


def print_crystal_summary(result: CrystalSimulationResult) -> None:
    """Print concise phase-matching and mode-matching summary."""
    phase = result.phase_matching
    mode = result.mode_matching
    bk_analysis = result.bk_analysis
    t_best = float(phase["T_best_K"][0])
    pm_best = float(phase["pm_power_best"][0])

    print("Crystal simulation summary")
    print("-------------------------")
    print(f"Geometry: {result.context.geometry}")
    phase_matching_type = phase.get("phase_matching_type")
    pump_axis = phase.get("pump_axis")
    signal_axis = phase.get("signal_axis")
    idler_axis = phase.get("idler_axis")
    if phase_matching_type is not None and pump_axis is not None and signal_axis is not None and idler_axis is not None:
        print(
            "Interaction type: "
            f"{phase_matching_type} ({pump_axis} -> {signal_axis} + {idler_axis})"
        )
    d_eff_pm_per_V = phase.get("d_eff_pm_per_V")
    if d_eff_pm_per_V is not None:
        print(f"Effective nonlinearity d_eff: {float(d_eff_pm_per_V):.6e} pm/V")
    print(f"Best phase-matching temperature: {t_best:.3f} K")
    print(f"Best phase-matching power factor: {pm_best:.6f}")
    print(f"Beam waist in crystal: {mode.waist_crystal_m*1e6:.3f} um")
    print(f"Rayleigh range in crystal: {mode.rayleigh_range_m*1e3:.3f} mm")
    print(f"Focusing parameter xi: {mode.focusing_parameter_xi:.6f}")
    print(f"Boyd-Kleinman factor: {mode.boyd_kleinman_factor:.6f}")
    print(f"Effective nonlinear overlap: {mode.effective_nonlinear_overlap:.6f}")

    phase_matching_operating_point = result.phase_matching_operating_point
    if phase_matching_operating_point is not None:
        print("Phase-matching operating point:")
        print(f"  temperature: {float(phase_matching_operating_point['temperature_K']):.3f} K")
        print(
            f"  phase-matching power factor: "
            f"{float(phase_matching_operating_point['phase_matching_power_factor']):.6f}"
        )
        print(
            f"  axes (signal/idler): {phase_matching_operating_point['signal_axis']} / "
            f"{phase_matching_operating_point['idler_axis']}"
        )
        print(
            f"  n(signal/idler): {float(phase_matching_operating_point['n_signal']):.6f} / "
            f"{float(phase_matching_operating_point['n_idler']):.6f}"
        )
        print(
            f"  wrapped phase mismatch: "
            f"{float(phase_matching_operating_point['wrapped_phase_mismatch_rad']):.6e} rad"
        )
        print(f"  double resonant: {bool(phase_matching_operating_point['is_double_resonant'])}")

    double_resonance_operating_point = result.double_resonance_operating_point
    if double_resonance_operating_point is not None:
        print("Double-resonance operating point:")
        print(f"  temperature: {float(double_resonance_operating_point['temperature_K']):.3f} K")
        print(f"  crystal length: {float(double_resonance_operating_point['crystal_length_m']) * 1e3:.3f} mm")
        print(
            f"  wrapped phase mismatch: "
            f"{float(double_resonance_operating_point['wrapped_phase_mismatch_rad']):.6e} rad"
        )
        print(
            f"  |wrapped phase mismatch|: "
            f"{float(double_resonance_operating_point['abs_wrapped_phase_mismatch_rad']):.6e} rad"
        )
        print(f"  double resonant: {bool(double_resonance_operating_point['is_double_resonant'])}")

    if result.selected_operating_point_mode is not None:
        print(f"Selected operating point mode: {result.selected_operating_point_mode}")
    if result.selected_operating_point is not None:
        print(f"Active operating temperature: {float(result.selected_operating_point['temperature_K']):.3f} K")
        active_crystal_length_m = float(result.selected_operating_point.get("crystal_length_m", result.context.crystal_length_m))
        if abs(active_crystal_length_m - float(result.context.crystal_length_m)) > _CRYSTAL_LENGTH_MATCH_TOLERANCE_M:
            print(
                "Selected crystal length differs from loaded cavity geometry; "
                f"rerun cavity with {active_crystal_length_m * 1e3:.6f} mm before OPO."
            )
    if result.active_polarization_resonance is not None:
        print("Active polarization-resonance diagnostic evaluated at selected operating temperature.")

    if bk_analysis is not None:
        reference = bk_analysis.get("reference", {})
        sigma_reference = reference.get("sigma_reference")
        xi_reference = reference.get("xi_reference")
        bk_master_sigma_opt = bk_analysis.get("bk_master_sigma_opt")
        bk_master_xi_opt = bk_analysis.get("bk_master_xi_opt")
        bk_master_h_opt = bk_analysis.get("bk_master_h_opt")

        if sigma_reference is not None and xi_reference is not None:
            print(f"BK reference point (sigma, xi): ({float(sigma_reference):.6f}, {float(xi_reference):.6f})")
        if bk_master_sigma_opt is not None and bk_master_xi_opt is not None:
            print(
                "BK master-map optimum (sigma, xi): "
                f"({float(bk_master_sigma_opt):.6f}, {float(bk_master_xi_opt):.6f})"
            )
        if bk_master_h_opt is not None:
            print(f"BK master-map optimum factor: {float(bk_master_h_opt):.6f}")


def _build_crystal_inputs_payload(context: CrystalContext) -> dict[str, Any]:
    return {
        "cavity_output_path": context.cavity_output_path,
        "crystal_length_m": context.crystal_length_m,
        "wavelength_m": context.wavelength_m,
        "n_crystal": context.n_crystal,
        "beam_waist_crystal_m": context.beam_waist_crystal_m,
    }


def _build_mode_matching_payload(mode_matching: ModeMatchingResult) -> dict[str, float]:
    return {
        "focusing_parameter_xi": float(mode_matching.focusing_parameter_xi),
        "boyd_kleinman_factor": float(mode_matching.boyd_kleinman_factor),
        "effective_nonlinear_overlap": float(mode_matching.effective_nonlinear_overlap),
    }


def _build_mode_matching_debug_payload(mode_matching: ModeMatchingResult) -> dict[str, float]:
    return asdict(mode_matching)


def _build_mode_matching_active_payload(mode_matching: ModeMatchingResult) -> dict[str, float]:
    return {
        "waist_crystal_m": float(mode_matching.waist_crystal_m),
        "rayleigh_range_m": float(mode_matching.rayleigh_range_m),
        "confocal_parameter_m": float(mode_matching.confocal_parameter_m),
        "focusing_parameter_xi": float(mode_matching.focusing_parameter_xi),
        "boyd_kleinman_factor": float(mode_matching.boyd_kleinman_factor),
        "effective_nonlinear_overlap": float(mode_matching.effective_nonlinear_overlap),
    }


def _strip_bk_map_payload(value: Any, store_bk_map: bool) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_bk_map_payload(item, store_bk_map)
            for key, item in value.items()
            if store_bk_map or key not in _BK_MAP_KEYS
        }
    if isinstance(value, list):
        return [_strip_bk_map_payload(item, store_bk_map) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_bk_map_payload(item, store_bk_map) for item in value)
    return value


def _build_bk_summary_payload(
    bk_analysis: dict[str, Any],
    *,
    store_bk_map: bool,
) -> dict[str, Any]:
    reference = bk_analysis.get("reference", {})
    payload = {
        "store_bk_map": bool(store_bk_map),
    }
    if reference:
        payload["reference"] = {
            key: reference[key]
            for key in (
                "reference_kind",
                "T_opt_K",
                "crystal_length_m",
                "xi_reference",
                "sigma_reference",
                "bk_reference_factor",
            )
            if key in reference
        }
    for key in ("bk_master_sigma_opt", "bk_master_xi_opt", "bk_master_h_opt"):
        if key in bk_analysis:
            payload[key] = bk_analysis[key]
    if store_bk_map:
        operating = bk_analysis.get("bk_analysis_operating", {})
        for key in _BK_MAP_KEYS:
            if key in operating:
                payload[key] = operating[key]
    return payload


def _build_bk_debug_payload(
    bk_analysis: dict[str, Any],
    *,
    store_bk_map: bool,
) -> dict[str, Any]:
    payload = _build_bk_summary_payload(bk_analysis, store_bk_map=store_bk_map)
    for key in ("bk_analysis_operating", "bk_analysis_optimal"):
        if key in bk_analysis:
            payload[key] = _strip_bk_map_payload(bk_analysis[key], store_bk_map=store_bk_map)
    return payload


def _build_active_for_opo_payload(
    result: CrystalSimulationResult,
    *,
    store_bk_map: bool,
) -> dict[str, Any] | None:
    if result.selected_operating_point_mode is None:
        return None

    cavity_crystal_length_m = float(result.context.crystal_length_m)
    selected_operating_point = result.selected_operating_point or {}
    active_crystal_length_m = float(selected_operating_point.get("crystal_length_m", cavity_crystal_length_m))
    active_for_opo = {
        "operating_point_mode": result.selected_operating_point_mode,
        "temperature_K": float(selected_operating_point.get("temperature_K", np.nan)),
        "crystal_length_m": active_crystal_length_m,
        "phase_matching": (
            {
                key: result.selected_operating_phase_matching[key]
                for key in (
                    "T_K",
                    "n_p",
                    "n_s",
                    "n_i",
                    "delta_k_rad_per_m",
                    "delta_k_eff_rad_per_m",
                    "pm_power",
                    "phase_matching_type",
                    "pump_axis",
                    "signal_axis",
                    "idler_axis",
                    "d_eff_pm_per_V",
                )
                if result.selected_operating_phase_matching is not None and key in result.selected_operating_phase_matching
            }
            if result.selected_operating_phase_matching is not None
            else None
        ),
        "mode_matching": _build_mode_matching_active_payload(result.mode_matching),
        "boyd_kleinman_analysis": (
            _build_bk_summary_payload(result.bk_analysis, store_bk_map=store_bk_map)
            if result.bk_analysis is not None
            else None
        ),
        "polarization_resonance": result.active_polarization_resonance,
        "cavity_crystal_length_m": cavity_crystal_length_m,
        "crystal_length_matches_cavity": bool(
            abs(active_crystal_length_m - cavity_crystal_length_m) <= _CRYSTAL_LENGTH_MATCH_TOLERANCE_M
        ),
        "recommended_cavity_crystal_length_m": active_crystal_length_m,
    }
    return {key: value for key, value in active_for_opo.items() if value is not None}


def _build_crystal_results_payload(
    result: CrystalSimulationResult,
    *,
    store_bk_map: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if result.selected_operating_point_mode is not None:
        payload["selected_operating_point_mode"] = result.selected_operating_point_mode
    if result.selected_operating_point is not None:
        payload["selected_operating_point"] = result.selected_operating_point
    payload["mode_matching"] = _build_mode_matching_payload(result.mode_matching)
    if result.bk_analysis is not None:
        payload["boyd_kleinman_analysis"] = _build_bk_summary_payload(
            result.bk_analysis,
            store_bk_map=store_bk_map,
        )
    if result.active_polarization_resonance is not None:
        payload["polarization_resonance"] = result.active_polarization_resonance
    active_for_opo = _build_active_for_opo_payload(result, store_bk_map=store_bk_map)
    if active_for_opo is not None:
        payload["active_for_opo"] = active_for_opo
    return payload


def _build_double_resonance_scan_payload(
    scan: dict[str, Any],
    include_full_matrices: bool = False,
) -> dict[str, Any]:
    payload = {
        "temperature_grid_K": scan["temperature_grid_K"],
        "crystal_length_grid_m": scan["crystal_length_grid_m"],
        "resonance_tolerance_rad": float(scan["resonance_tolerance_rad"]),
        "best_temperature_K": float(scan["best_temperature_K"]),
        "best_crystal_length_m": float(scan["best_crystal_length_m"]),
        "best_delta_phi_wrapped_rad": float(scan["best_delta_phi_wrapped_rad"]),
        "best_abs_delta_phi_wrapped_rad": float(scan["best_abs_delta_phi_wrapped_rad"]),
        "best_is_double_resonant": bool(scan["best_is_double_resonant"]),
    }
    if include_full_matrices:
        payload["delta_phi_wrapped_rad"] = scan["delta_phi_wrapped_rad"]
        payload["abs_delta_phi_wrapped_rad"] = scan["abs_delta_phi_wrapped_rad"]
        payload["is_double_resonant"] = scan["is_double_resonant"]
    return payload


def _build_crystal_debug_payload(
    result: CrystalSimulationResult,
    *,
    save_full_double_resonance_scan: bool = False,
    store_bk_map: bool = False,
) -> dict[str, Any]:
    payload = {}
    payload["mode_matching"] = _build_mode_matching_debug_payload(result.mode_matching)
    if result.selected_operating_phase_matching is not None:
        payload["active_phase_matching"] = result.selected_operating_phase_matching
    operating_points = {}
    if result.phase_matching_operating_point is not None:
        operating_points["phase_matching_operating_point"] = result.phase_matching_operating_point
    if result.double_resonance_operating_point is not None:
        operating_points["double_resonance_operating_point"] = result.double_resonance_operating_point
    if operating_points:
        payload["operating_points"] = operating_points
    if result.polarization_resonance is not None:
        payload["phase_matching_polarization_resonance"] = result.polarization_resonance
    if result.phase_matching is not None:
        payload["phase_matching_scan"] = result.phase_matching
    if result.double_resonance_scan is not None:
        payload["double_resonance_scan"] = _build_double_resonance_scan_payload(
            result.double_resonance_scan,
            include_full_matrices=save_full_double_resonance_scan,
        )
    if result.bk_analysis is not None:
        payload["boyd_kleinman_analysis"] = _build_bk_debug_payload(
            result.bk_analysis,
            store_bk_map=store_bk_map,
        )
    return payload


def build_crystal_simulation_output(
    result: CrystalSimulationResult,
    save_full_double_resonance_scan: bool = False,
    debug: bool = False,
    store_bk_map: bool = False,
) -> dict[str, Any]:
    """Build JSON-serializable crystal simulation output."""
    output = {
        "inputs": {
            "geometry": result.context.geometry,
            **_build_crystal_inputs_payload(result.context),
        },
        "results": _build_crystal_results_payload(
            result,
            store_bk_map=store_bk_map,
        ),
    }
    if debug:
        debug_payload = _build_crystal_debug_payload(
            result,
            save_full_double_resonance_scan=save_full_double_resonance_scan,
            store_bk_map=store_bk_map,
        )
        if debug_payload:
            output["debug_data"] = debug_payload
    return output


def save_crystal_outputs(
    geometry: str,
    output: dict[str, Any],
    fig_bk_master=None,
    fig_qpm=None,
    fig_bk=None,
    results_root: str | Path | None = None,
    fig_bk_optimal=None,
    fig_double_resonance_scan=None,
) -> dict[str, str]:
    """Save crystal JSON and plots under ``results/<geometry>/crystal/``."""
    ensure_geometry_results_subdirs(geometry, results_root=results_root)
    result_dir = get_crystal_results_dir(geometry, results_root=results_root)
    project_root = Path(__file__).resolve().parents[2]

    json_path = result_dir / "crystal_simulation_output.json"
    bk_master_path = result_dir / "boyd_kleinman_master_map.png"
    qpm_path = result_dir / "qpm_length_poling_map.png"
    bk_path = result_dir / "boyd_kleinman_analysis.png"
    bk_optimal_path = result_dir / "boyd_kleinman_analysis_optimal.png"
    double_resonance_scan_path = result_dir / "double_resonance_scan.png"
    old_phase_path = result_dir / "phase_matching_scan.png"
    old_mode_path = result_dir / "mode_matching_summary.png"

    def _repo_relative(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(project_root))
        except ValueError:
            return str(path)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(_to_json_compatible(output), f, indent=2)

    # Remove legacy plot files so the crystal results directory reflects the
    # current single-figure BK workflow after a fresh save.
    for legacy_path in (old_phase_path, old_mode_path):
        if legacy_path.exists():
            legacy_path.unlink()

    if fig_bk_master is not None:
        fig_bk_master.savefig(bk_master_path, dpi=300, bbox_inches="tight")
    if fig_qpm is not None:
        fig_qpm.savefig(qpm_path, dpi=300, bbox_inches="tight")
    if fig_bk is not None:
        fig_bk.savefig(bk_path, dpi=300, bbox_inches="tight")
    if fig_bk_optimal is not None:
        fig_bk_optimal.savefig(bk_optimal_path, dpi=300, bbox_inches="tight")
    if fig_double_resonance_scan is not None:
        fig_double_resonance_scan.savefig(double_resonance_scan_path, dpi=300, bbox_inches="tight")

    outputs = {
        "result_dir": _repo_relative(result_dir),
        "crystal_output_json": _repo_relative(json_path),
    }
    if fig_bk_master is not None:
        outputs["boyd_kleinman_master_map_png"] = _repo_relative(bk_master_path)
    if fig_qpm is not None:
        outputs["qpm_length_poling_map_png"] = _repo_relative(qpm_path)
    if fig_bk is not None:
        bk_relpath = _repo_relative(bk_path)
        outputs["boyd_kleinman_analysis_png"] = bk_relpath
        outputs["phase_matching_scan_png"] = bk_relpath
        outputs["mode_matching_summary_png"] = bk_relpath
    if fig_bk_optimal is not None:
        outputs["boyd_kleinman_analysis_optimal_png"] = _repo_relative(bk_optimal_path)
    if fig_double_resonance_scan is not None:
        outputs["double_resonance_scan_png"] = _repo_relative(double_resonance_scan_path)
    return outputs


__all__ = [
    "CrystalContext",
    "CrystalSimulationResult",
    "load_cavity_context_for_crystal",
    "compute_crystal_phase_matching",
    "compute_design_poling_period",
    "compute_crystal_mode_matching",
    "compute_boyd_kleinman_analysis",
    "build_phase_matching_operating_point",
    "build_double_resonance_operating_point",
    "select_crystal_operating_point",
    "build_crystal_simulation_result",
    "build_crystal_simulation_output",
    "print_crystal_summary",
    "save_crystal_outputs",
]
