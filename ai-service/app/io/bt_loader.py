"""Loading brightness-temperature arrays from disk.

Structural metrics need Kelvin values, not display pixels, so we read the ``.npy``
arrays written by ``ml/ingest/render_frames.py`` rather than the PNGs shown in the UI.
Quantising to 8-bit for display loses roughly half a Kelvin per level, which is enough to
move the eye-contrast and CDO-fraction thresholds around.

Every path is resolved under ``FRAMES_DIR`` and checked, because these paths arrive over
HTTP from another service.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from loguru import logger


class FrameNotAvailable(Exception):
    """No brightness-temperature array exists for this frame."""


def load_bt(frames_dir: Path, bt_path: str | None) -> np.ndarray | None:
    """Load a brightness-temperature array, or return ``None`` if there is none.

    Args:
        frames_dir: the configured root. Nothing outside it can be read.
        bt_path: path relative to ``frames_dir``.

    Returns:
        A 2-D float array in Kelvin, or ``None`` when the frame has no imagery. A frame
        without imagery is normal — not every best-track point has a matched satellite
        observation — so it is a return value rather than an error.

    Raises:
        FrameNotAvailable: if the path escapes ``frames_dir`` or the file is unreadable.
    """
    if not bt_path:
        return None

    root = frames_dir.resolve()
    candidate = (root / bt_path).resolve()

    if not candidate.is_relative_to(root):
        raise FrameNotAvailable(
            f"refusing to read outside the frames directory: {bt_path!r}"
        )

    if not candidate.exists():
        logger.debug("no brightness-temperature array at {}", candidate)
        return None

    try:
        array = np.load(candidate)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a clean error
        raise FrameNotAvailable(f"could not read {bt_path!r}: {exc}") from exc

    if array.ndim != 2:
        raise FrameNotAvailable(
            f"expected a 2-D brightness-temperature field in {bt_path!r}, "
            f"got shape {array.shape}"
        )

    return array.astype(float)
