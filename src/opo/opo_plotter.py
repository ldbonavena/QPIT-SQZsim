"""Plotting helpers for OPO operating-point and squeezing-spectrum views."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_opo_spectrum_summary(spectrum: dict[str, list[float]]):
    """Plot squeezing, antisqueezing, and shot-noise reference spectra."""
    frequency_hz = np.asarray(spectrum["frequency_Hz"], dtype=float)
    squeezing = np.maximum(np.asarray(spectrum["squeezing_spectrum"], dtype=float), np.finfo(float).eps)
    antisqueezing = np.maximum(np.asarray(spectrum["antisqueezing_spectrum"], dtype=float), np.finfo(float).eps)
    measured = np.maximum(
        np.asarray(spectrum.get("measured_quadrature_spectrum", spectrum["squeezing_spectrum"]), dtype=float),
        np.finfo(float).eps,
    )
    shot_noise = np.maximum(np.asarray(spectrum["shot_noise_reference"], dtype=float), np.finfo(float).eps)
    theta = float(spectrum.get("lo_phase_rad", 0.0))

    squeezing_db = 10.0 * np.log10(squeezing)
    antisqueezing_db = 10.0 * np.log10(antisqueezing)
    measured_db = 10.0 * np.log10(measured)
    shot_noise_db = 10.0 * np.log10(shot_noise)

    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.plot(frequency_hz, squeezing_db, lw=2.8, label="Squeezing")
    ax.plot(frequency_hz, antisqueezing_db, lw=2.8, label="Antisqueezing")
    ax.plot(frequency_hz, measured_db, "--", lw=2.4, label=fr"Measured ($\theta={theta:.2f}$ rad)")
    ax.plot(frequency_hz, shot_noise_db, "--", lw=1.6, color="#666666", label="Shot noise")
    ax.axhline(0.0, color="#666666", ls="--", lw=1.0, alpha=0.6)

    ax.set_xlabel("Analysis frequency [Hz]")
    ax.set_ylabel("Noise [dB]")
    ax.set_title("OPO squeezing spectrum", fontsize=15, fontweight="semibold", pad=10)

    ax.set_facecolor("white")
    ax.grid(True, color="#b0b0b0", alpha=0.5, linewidth=0.8)
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=10, loc="best")

    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.14, top=0.90)
    return fig

__all__ = [
    "plot_opo_spectrum_summary",
]
