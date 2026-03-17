import os
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    camera_ip: str
    camera_stream: str
    tapo_user: str
    tapo_password: str
    interval_seconds: int
    jpeg_quality: int
    session_name: str
    frames_dir: str
    logs_dir: str
    log_level: str
    log_max_bytes: int
    log_backup_count: int


def load_config(config_path: str = "config.yaml") -> Config:
    load_dotenv()

    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        sys.exit(f"ERROR: config file not found: {config_path}")
    except yaml.YAMLError as e:
        sys.exit(f"ERROR: failed to parse {config_path}: {e}")

    errors = []

    tapo_user = os.environ.get("TAPO_USER", "").strip()
    tapo_password = os.environ.get("TAPO_PASSWORD", "").strip()
    if not tapo_user:
        errors.append("TAPO_USER is not set in .env")
    if not tapo_password:
        errors.append("TAPO_PASSWORD is not set in .env")

    try:
        camera_ip = cfg["camera"]["ip"]
        if not camera_ip:
            errors.append("camera.ip is empty in config.yaml")
    except KeyError:
        errors.append("camera.ip is missing from config.yaml")
        camera_ip = ""

    try:
        camera_stream = cfg["camera"]["stream"]
    except KeyError:
        errors.append("camera.stream is missing from config.yaml")
        camera_stream = "stream1"

    try:
        interval_seconds = int(cfg["capture"]["interval_seconds"])
        if interval_seconds < 1:
            errors.append("capture.interval_seconds must be >= 1")
    except (KeyError, TypeError, ValueError):
        errors.append("capture.interval_seconds is missing or invalid in config.yaml")
        interval_seconds = 30

    try:
        jpeg_quality = int(cfg["capture"]["jpeg_quality"])
        if not (1 <= jpeg_quality <= 100):
            errors.append("capture.jpeg_quality must be between 1 and 100")
    except (KeyError, TypeError, ValueError):
        errors.append("capture.jpeg_quality is missing or invalid in config.yaml")
        jpeg_quality = 85

    session_name = cfg.get("capture", {}).get("session_name", "") or ""
    frames_dir = cfg.get("output", {}).get("frames_dir", "/frames")
    logs_dir = cfg.get("output", {}).get("logs_dir", "/logs")

    log_level = cfg.get("logging", {}).get("level", "INFO").upper()
    log_max_bytes = int(cfg.get("logging", {}).get("max_bytes", 5242880))
    log_backup_count = int(cfg.get("logging", {}).get("backup_count", 3))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    return Config(
        camera_ip=str(camera_ip),
        camera_stream=str(camera_stream),
        tapo_user=tapo_user,
        tapo_password=tapo_password,
        interval_seconds=interval_seconds,
        jpeg_quality=jpeg_quality,
        session_name=session_name,
        frames_dir=frames_dir,
        logs_dir=logs_dir,
        log_level=log_level,
        log_max_bytes=log_max_bytes,
        log_backup_count=log_backup_count,
    )
