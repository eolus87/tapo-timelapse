import logging

import cv2

logger = logging.getLogger(__name__)


class RTSPCamera:
    def __init__(self, ip: str, stream: str, user: str, password: str):
        self._url = f"rtsp://{user}:{password}@{ip}:554/{stream}"
        self._cap: cv2.VideoCapture | None = None

    def connect(self) -> bool:
        self.disconnect()
        cap = cv2.VideoCapture(self._url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            cap.release()
            return False
        self._cap = cap
        return True

    def disconnect(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def grab_frame(self) -> bytes | None:
        if self._cap is None:
            return None
        # Drain the internal buffer by calling grab() several times,
        # then retrieve the most recent frame.
        for _ in range(5):
            if not self._cap.grab():
                return None
        ret, frame = self._cap.retrieve()
        if not ret or frame is None:
            return None
        return frame

    def __enter__(self) -> "RTSPCamera":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()
