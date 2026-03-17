import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_FRAME_RE = re.compile(r"^frame_(\d+)_\d{8}_\d{6}\.jpg$")


class FrameStorage:
    def __init__(self, frames_dir: str, jpeg_quality: int):
        self._jpeg_quality = jpeg_quality
        self._session_dir = Path(frames_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._counter = self._resume_counter()
        logger.info("Frames directory: %s (starting at frame %d)", self._session_dir, self._counter)

    def _resume_counter(self) -> int:
        max_num = 0
        for f in self._session_dir.iterdir():
            m = _FRAME_RE.match(f.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
        return max_num + 1 if max_num else 1

    def save(self, frame: np.ndarray) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"frame_{self._counter:06d}_{ts}.jpg"
        path = self._session_dir / filename
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
        cv2.imwrite(str(path), frame, encode_params)
        self._counter += 1
        return filename
