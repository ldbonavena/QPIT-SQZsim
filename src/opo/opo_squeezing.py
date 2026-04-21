"""Frequency-domain squeezing spectra built from the OPO Langevin scaffold.

This module defines the analysis-frequency grid and evaluates a compact
below-threshold degenerate OPO noise model from the existing linearized
Langevin state-space matrices.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .opo_langevin import OPOLangevinModel
from .opo_model import OPOModelResult, OPOParameters


@dataclass(frozen=True)
class OPOSqueezingSpectrum:
    """Frequency-domain OPO squeezing output."""

    frequency_Hz: np.ndarray
    squeezing_spectrum: np.ndarray
    antisqueezing_spectrum: np.ndarray
    measured_quadrature_spectrum: np.ndarray
    shot_noise_reference: np.ndarray
    optimal_phase_rad: np.ndarray
    lo_phase_rad: float
    notes: tuple[str, ...]


def _compute_minimal_output_spectral_density(
    drift_matrix: np.ndarray,
    input_matrix: np.ndarray,
    noise_coupling_matrix: np.ndarray,
    linewidth_rad_s: float,
    omega_rad_s: float,
) -> np.ndarray:
    """Return a compact output spectral density for the current 2x2 model.

    This helper is intentionally minimal and only targets the present
    below-threshold 2x2 quadrature model. It should not be interpreted as a
    full general quantum input-output construction.
    """
    identity = np.eye(drift_matrix.shape[0], dtype=complex)
    response = np.linalg.inv(1j * float(omega_rad_s) * identity - drift_matrix.astype(complex))
    coupling_scale = np.sqrt(2.0 * float(linewidth_rad_s))
    effective_input = coupling_scale * input_matrix.astype(complex)
    effective_noise = coupling_scale * noise_coupling_matrix.astype(complex)
    output_transfer = identity - effective_input @ response @ effective_noise
    return output_transfer @ output_transfer.T.conj()


def _high_frequency_reference(values: np.ndarray) -> float:
    """Estimate the asymptotic high-frequency reference from the tail of one spectrum."""
    n_points = values.size
    tail_count = max(1, int(np.ceil(0.1 * n_points)))
    tail_mean = float(np.mean(values[-tail_count:]))
    return max(tail_mean, np.finfo(float).eps)


def build_analysis_frequency_grid(parameters: OPOParameters) -> np.ndarray:
    """Build the analysis-frequency axis used for spectrum calculations."""
    f_min, f_max = parameters.analysis_span_Hz
    if parameters.n_analysis_points < 2:
        raise ValueError("n_analysis_points must be at least 2")
    if f_min < 0.0 or f_max <= f_min:
        raise ValueError("analysis_span_Hz must satisfy 0 <= f_min < f_max")
    return np.linspace(f_min, f_max, parameters.n_analysis_points, dtype=float)


def compute_squeezing_spectra(
    parameters: OPOParameters,
    model: OPOModelResult,
    langevin: OPOLangevinModel,
) -> OPOSqueezingSpectrum:
    """Return below-threshold quadrature spectra from the Langevin matrices."""

    frequency_hz = build_analysis_frequency_grid(parameters)
    shot_noise = np.ones_like(frequency_hz, dtype=float)

    sigma = float(model.pump_parameter)
    if sigma >= 1.0:
        raise ValueError(
            "compute_squeezing_spectra only supports the below-threshold model with sigma < 1. "
            f"Received sigma={sigma:.6f}."
        )

    eta_esc = float(np.clip(model.escape_efficiency, 0.0, 1.0))
    eta_det = float(np.clip(parameters.detection_efficiency, 0.0, 1.0))
    theta = float(parameters.lo_phase_rad)
    measurement_vector = np.array([np.cos(theta), np.sin(theta)], dtype=float)

    omega = 2.0 * np.pi * frequency_hz
    linewidth_rad_s = max(2.0 * np.pi * max(float(model.cavity_kappa_total_Hz), 0.0), np.finfo(float).eps)

    drift_matrix = np.asarray(langevin.drift_matrix, dtype=float)
    input_matrix = np.asarray(langevin.input_matrix, dtype=float)
    noise_coupling_matrix = np.asarray(langevin.noise_coupling_matrix, dtype=float)

    quadrature_x_output = np.empty_like(frequency_hz, dtype=float)
    quadrature_p_output = np.empty_like(frequency_hz, dtype=float)
    measured_quadrature_output = np.empty_like(frequency_hz, dtype=float)
    optimal_phase_rad = np.empty_like(frequency_hz, dtype=float)
    failed_points = 0

    for i, omega_i in enumerate(omega):
        try:
            output_sd = _compute_minimal_output_spectral_density(
                drift_matrix,
                input_matrix,
                noise_coupling_matrix,
                linewidth_rad_s,
                omega_i,
            )
            s_xx = max(float(np.real_if_close(output_sd[0, 0])), 0.0)
            s_pp = max(float(np.real_if_close(output_sd[1, 1])), 0.0)
            s_xp = complex(output_sd[0, 1])
            s_px = complex(output_sd[1, 0])

            quadrature_x_output[i] = s_xx
            quadrature_p_output[i] = s_pp

            measured_value = np.real_if_close(measurement_vector @ output_sd @ measurement_vector)
            measured_quadrature_output[i] = max(float(measured_value), 0.0)

            symmetric_spectrum = np.array(
                [
                    [s_xx, float(np.real_if_close(0.5 * (s_xp + s_px)))],
                    [float(np.real_if_close(0.5 * (s_xp + s_px))), s_pp],
                ],
                dtype=float,
            )
            _, eigenvectors = np.linalg.eigh(symmetric_spectrum)
            optimal_phase_rad[i] = float(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))

            if (
                not np.isfinite(quadrature_x_output[i])
                or not np.isfinite(quadrature_p_output[i])
                or not np.isfinite(measured_quadrature_output[i])
                or not np.isfinite(optimal_phase_rad[i])
            ):
                raise FloatingPointError("Non-finite normalized spectrum value.")
        except (np.linalg.LinAlgError, ValueError, FloatingPointError):
            quadrature_x_output[i] = 1.0
            quadrature_p_output[i] = 1.0
            measured_quadrature_output[i] = 1.0
            optimal_phase_rad[i] = theta
            failed_points += 1

    quadrature_x_output = quadrature_x_output / _high_frequency_reference(quadrature_x_output)
    quadrature_p_output = quadrature_p_output / _high_frequency_reference(quadrature_p_output)
    measured_quadrature_output = measured_quadrature_output / _high_frequency_reference(measured_quadrature_output)

    quadrature_x_low = float(quadrature_x_output[0])
    quadrature_p_low = float(quadrature_p_output[0])
    if quadrature_x_low <= quadrature_p_low:
        squeezing_internal = quadrature_x_output
        antisqueezing_internal = quadrature_p_output
    else:
        squeezing_internal = quadrature_p_output
        antisqueezing_internal = quadrature_x_output

    squeezing_coupled = 1.0 - eta_esc + eta_esc * squeezing_internal
    antisqueezing_coupled = 1.0 - eta_esc + eta_esc * antisqueezing_internal
    measured_coupled = 1.0 - eta_esc + eta_esc * measured_quadrature_output

    # Detection loss mixes the output with vacuum and pulls both spectra
    # toward the shot-noise reference.
    squeezing = 1.0 - eta_det + eta_det * squeezing_coupled
    antisqueezing = 1.0 - eta_det + eta_det * antisqueezing_coupled
    measured = 1.0 - eta_det + eta_det * measured_coupled

    notes = [
        "Spectrum computed from a minimal output spectral-density construction in a 2x2 quadrature basis.",
        "The X/P quadratures are mixed by cavity detuning before squeezing and anti-squeezing labels are assigned.",
        "Squeezing and anti-squeezing labels are assigned from the low-frequency ordering of the quadrature spectra.",
        f"Measured quadrature defined by homodyne LO phase theta = {theta:.6f} rad.",
        "optimal_phase_rad stores the phase of the minimum-noise quadrature at each analysis frequency.",
        "Each quadrature spectrum is normalized to its high-frequency shot-noise asymptote.",
        f"Cavity detuning used in the quadrature response: {float(model.cavity_detuning_Hz):.6f} Hz.",
        "Escape efficiency and detection efficiency are included phenomenologically.",
    ]
    if failed_points:
        notes.append(
            f"{failed_points} frequency point(s) fell back to shot noise after a response-matrix inversion failure."
        )

    return OPOSqueezingSpectrum(
        frequency_Hz=frequency_hz,
        squeezing_spectrum=np.asarray(squeezing, dtype=float),
        antisqueezing_spectrum=np.asarray(antisqueezing, dtype=float),
        measured_quadrature_spectrum=np.asarray(measured, dtype=float),
        shot_noise_reference=shot_noise,
        optimal_phase_rad=np.asarray(optimal_phase_rad, dtype=float),
        lo_phase_rad=theta,
        notes=tuple(notes),
    )


def spectrum_to_dict(spectrum: OPOSqueezingSpectrum) -> dict[str, list[float] | list[str]]:
    """Convert the squeezing spectrum dataclass into a JSON-friendly mapping."""
    return {
        "frequency_Hz": spectrum.frequency_Hz.tolist(),
        "squeezing_spectrum": spectrum.squeezing_spectrum.tolist(),
        "antisqueezing_spectrum": spectrum.antisqueezing_spectrum.tolist(),
        "measured_quadrature_spectrum": spectrum.measured_quadrature_spectrum.tolist(),
        "shot_noise_reference": spectrum.shot_noise_reference.tolist(),
        "optimal_phase_rad": spectrum.optimal_phase_rad.tolist(),
        "lo_phase_rad": float(spectrum.lo_phase_rad),
        "notes": list(spectrum.notes),
    }


__all__ = [
    "OPOSqueezingSpectrum",
    "build_analysis_frequency_grid",
    "compute_squeezing_spectra",
    "spectrum_to_dict",
]
