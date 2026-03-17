import logging
import logging.handlers
import signal
import sys
import time
from pathlib import Path

from camera import RTSPCamera
from config import load_config
from storage import FrameStorage


def setup_logging(log_level: str, logs_dir: str, max_bytes: int, backup_count: int) -> None:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(logs_dir) / "capture.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    rotating = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    rotating.setFormatter(fmt)
    root.addHandler(rotating)


def main() -> None:
    config = load_config()
    setup_logging(config.log_level, config.logs_dir, config.log_max_bytes, config.log_backup_count)

    logger = logging.getLogger(__name__)
    logger.info("Starting tapo-timelapse capture service")

    storage = FrameStorage(config.frames_dir, config.jpeg_quality)
    camera = RTSPCamera(config.camera_ip, config.camera_stream, config.tapo_user, config.tapo_password)

    shutdown = False

    def handle_signal(signum, frame):
        nonlocal shutdown
        logger.info("Signal %d received, shutting down gracefully", signum)
        shutdown = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    backoff = 5
    backoff_max = 120
    camera_was_offline = False
    last_capture = time.monotonic() - config.interval_seconds  # capture immediately on start

    while not shutdown:
        # --- ensure camera is connected ---
        if camera._cap is None:
            logger.debug("Attempting to connect to camera…")
            if not camera.connect():
                if not camera_was_offline:
                    logger.warning("Camera is offline or unreachable — will keep retrying")
                    camera_was_offline = True
                else:
                    logger.debug("Still offline, next retry in %ds", backoff)
                _interruptible_sleep(backoff, lambda: shutdown)
                backoff = min(backoff * 2, backoff_max)
                continue
            # connected (possibly recovered)
            if camera_was_offline:
                logger.info("Camera back online")
                camera_was_offline = False
            backoff = 5

        # --- wait until next capture is due ---
        now = time.monotonic()
        wait = last_capture + config.interval_seconds - now
        if wait > 0:
            _interruptible_sleep(wait, lambda: shutdown)
            if shutdown:
                break

        # --- grab frame ---
        frame = camera.grab_frame()
        if frame is None:
            logger.debug("Frame grab failed, reconnecting…")
            camera.disconnect()
            if not camera_was_offline:
                logger.warning("Camera went offline mid-session — will keep retrying")
                camera_was_offline = True
            _interruptible_sleep(backoff, lambda: shutdown)
            backoff = min(backoff * 2, backoff_max)
            continue

        last_capture = time.monotonic()
        try:
            filename = storage.save(frame)
            logger.info("Saved frame %s", filename)
        except Exception as e:
            logger.error("Failed to save frame: %s", e)

    camera.disconnect()
    logger.info("Capture service stopped")


def _interruptible_sleep(seconds: float, should_stop) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if should_stop():
            return
        time.sleep(0.2)


if __name__ == "__main__":
    main()
