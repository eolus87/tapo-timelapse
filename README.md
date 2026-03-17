# tapo-timelapse

A lightweight service that connects to a Tapo camera over RTSP and captures frames at a configurable interval, saving them to disk for timelapse creation. Designed to run continuously as a Docker container with automatic reconnection if the camera goes offline.

## Features

- Connects to Tapo cameras via RTSP (HD or sub-stream)
- Configurable capture interval and JPEG quality
- Automatically reconnects with exponential backoff if the camera drops
- Rotating log files to avoid filling up disk
- Graceful shutdown on `SIGTERM` / `SIGINT`
- Runs headless — no display required

## Project structure

```
main.py          # Entry point and capture loop
camera/          # RTSP camera connection and frame grabbing
config/          # Configuration loading and validation
storage/         # Frame saving and session management
config.example.yaml
docker-compose.example.yml
Dockerfile
```

## Requirements

- Python 3.11+
- [Pipenv](https://pipenv.pypa.io/)
- A Tapo camera accessible on the local network via RTSP

**Python dependencies** (managed via Pipenv):

| Package | Version |
|---|---|
| opencv-python-headless | 4.9.0.80 |
| numpy | >=1.17.3, <2.0 |
| python-dotenv | 1.0.1 |
| PyYAML | 6.0.1 |

## Configuration

### 1. Credentials — `.env`

Create a `.env` file in the project root:

```env
TAPO_USER=your_tapo_username
TAPO_PASSWORD=your_tapo_password
```

> These are your Tapo camera credentials (set in the Tapo app). This file is gitignored and never committed.

### 2. Config — `config.yaml`

Copy the example and edit it:

```bash
cp config.example.yaml config.yaml
```

```yaml
camera:
  ip: 192.168.1.100
  stream: stream1        # stream1 = HD, stream2 = sub-stream (lower res/CPU)

capture:
  interval_seconds: 30   # seconds between frames
  jpeg_quality: 85       # 1-100
  session_name: ""       # leave blank to auto-generate from startup timestamp

output:
  frames_dir: /frames    # inside container — mount to any host path
  logs_dir: /logs        # inside container — mount to any host path

logging:
  level: INFO            # DEBUG, INFO, WARNING, ERROR
  max_bytes: 5242880     # 5 MB per log file
  backup_count: 3        # number of rotated files to keep
```

## Running

### With Docker (recommended)

Copy the example compose file and adjust the volume paths:

```bash
cp docker-compose.example.yml docker-compose.yml
```

Edit the host-side volume paths in `docker-compose.yml` to point to where you want frames and logs stored, then build and start the container:

```bash
docker compose build
docker compose up -d
```

Or in one step:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

### Locally with Pipenv

```bash
pipenv install
pipenv run python main.py
```

## Frame output

Frames are saved under the configured `frames_dir`, organised into session subdirectories named by start timestamp:

```
frames/
  20260317_151656/
    frame_000001_20260317_152559.jpg
    frame_000002_20260317_152629.jpg
    ...
```

If the service restarts, it resumes the frame counter from the last saved frame in the session directory.

## Resource limits

The included Docker Compose example caps the container at **0.5 CPU** and **256 MB RAM**, which is sufficient for most capture intervals. Adjust in `docker-compose.yml` if needed.

## License

MIT
