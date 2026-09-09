"""Polar regridding of a storm-centred brightness-temperature field.

Every structural metric is an azimuthal statistic — how cold the cloud tops are at a
given radius, how much that varies with angle, where the convective ring sits. Those are
awkward on a Cartesian grid and natural on a polar one, so we resample once here and let
the metrics work in (radius, angle) space.

The input is expected in Kelvin, storm-centred, with a known pixel size. HURSAT-B1
IRWIN fields are ~8 km per pixel on a 301x301 grid; INSAT-3D differs, which is why the
pixel size is a parameter rather than a constant.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Deep convection in the tropics. The exact cut is tuned in Phase 2 on held-out data;
# the literature range is roughly 208-220 K, so this is a starting point, not a claim.
DEEP_CONVECTION_K = 220.0

# Very cold overshooting tops, used for the cold-cloud centroid.
COLD_CLOUD_K = 210.0


@dataclass(frozen=True)
class PolarField:
    """A storm-centred field resampled onto a polar grid.

    Attributes:
        values: shape (n_r, n_theta), Kelvin. NaN where the sample fell outside the grid.
        radii_km: shape (n_r,), the radius of each ring in kilometres.
        theta: shape (n_theta,), angles in radians.
    """

    values: np.ndarray
    radii_km: np.ndarray
    theta: np.ndarray

    def ring(self, radius_km: float) -> np.ndarray:
        """The azimuthal series at the ring nearest ``radius_km``."""
        idx = int(np.argmin(np.abs(self.radii_km - radius_km)))
        return self.values[idx]

    def azimuthal_mean(self) -> np.ndarray:
        """Mean brightness temperature per radius, ignoring NaN."""
        with np.errstate(invalid="ignore"):
            return np.nanmean(self.values, axis=1)

    def mask_within(self, radius_km: float) -> np.ndarray:
        return self.radii_km <= radius_km


def to_polar(
    bt: np.ndarray,
    km_per_pixel: float,
    *,
    r_max_km: float = 300.0,
    n_r: int = 60,
    n_theta: int = 72,
    centre: tuple[float, float] | None = None,
) -> PolarField:
    """Resample a Cartesian BT field onto a polar grid by bilinear interpolation.

    Args:
        bt: 2-D array of brightness temperature in Kelvin.
        km_per_pixel: ground resolution of one pixel.
        r_max_km: outermost radius to sample.
        n_r: number of radial rings.
        n_theta: number of azimuthal samples per ring. 72 gives 5-degree resolution,
            which is ample for the wavenumber-1 decomposition and cheap enough to run
            on every frame of every storm during precomputation.
        centre: (row, col) of the storm centre. Defaults to the array centre, which is
            correct for storm-centred products such as HURSAT-B1.

    Returns:
        The resampled field. Samples that fall outside the input grid are NaN rather
        than clamped, so an undersized input degrades to missing data instead of
        silently repeating its edge pixels.
    """
    if bt.ndim != 2:
        raise ValueError(f"expected a 2-D brightness-temperature field, got shape {bt.shape}")
    if km_per_pixel <= 0:
        raise ValueError(f"km_per_pixel must be positive, got {km_per_pixel}")

    rows, cols = bt.shape
    cr, cc = ((rows - 1) / 2.0, (cols - 1) / 2.0) if centre is None else centre

    radii_km = np.linspace(0.0, r_max_km, n_r)
    theta = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)

    r_grid, t_grid = np.meshgrid(radii_km, theta, indexing="ij")
    r_px = r_grid / km_per_pixel
    # Row index grows downward; negative sine keeps theta measured anticlockwise from east.
    sample_r = cr - r_px * np.sin(t_grid)
    sample_c = cc + r_px * np.cos(t_grid)

    values = _bilinear_sample(bt, sample_r, sample_c)
    return PolarField(values=values, radii_km=radii_km, theta=theta)


def _bilinear_sample(field: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Bilinear interpolation with NaN outside the grid."""
    h, w = field.shape

    r0 = np.floor(rows).astype(int)
    c0 = np.floor(cols).astype(int)
    r1 = r0 + 1
    c1 = c0 + 1

    inside = (r0 >= 0) & (c0 >= 0) & (r1 < h) & (c1 < w)

    r0c = np.clip(r0, 0, h - 1)
    r1c = np.clip(r1, 0, h - 1)
    c0c = np.clip(c0, 0, w - 1)
    c1c = np.clip(c1, 0, w - 1)

    dr = rows - r0
    dc = cols - c0

    top = field[r0c, c0c] * (1 - dc) + field[r0c, c1c] * dc
    bottom = field[r1c, c0c] * (1 - dc) + field[r1c, c1c] * dc
    out = top * (1 - dr) + bottom * dr

    return np.where(inside, out, np.nan)


def background_temperature(
    bt: np.ndarray, km_per_pixel: float, *, inner_km: float = 200.0, outer_km: float = 300.0
) -> float:
    """Environmental brightness temperature, taken from an outer annulus.

    Structural metrics describe the storm, not the scene it sits in. Subtracting this
    background is what makes the wavenumber decomposition comparable between a frame
    over a warm ocean and one over a cooler one.
    """
    rows, cols = bt.shape
    cr, cc = (rows - 1) / 2.0, (cols - 1) / 2.0
    rr, cc_idx = np.ogrid[:rows, :cols]
    dist_km = np.hypot(rr - cr, cc_idx - cc) * km_per_pixel

    annulus = bt[(dist_km >= inner_km) & (dist_km <= outer_km)]
    annulus = annulus[np.isfinite(annulus)]
    if annulus.size == 0:
        finite = bt[np.isfinite(bt)]
        return float(np.median(finite)) if finite.size else float("nan")
    return float(np.median(annulus))
