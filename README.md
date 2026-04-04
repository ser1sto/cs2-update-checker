# CS2 Update Checker

A lightweight bot that monitors the CS2 RSS feed for new updates and sends notifications via Discord webhook, ntfy, and e-mail. Designed to run 24/7 on a Raspberry Pi using Docker.

## Features

- Monitors the CS2 RSS feed for new patch notes
- Sends notifications via:
  - Discord webhook
  - ntfy push notifications
  - E-mail (SMTP) – useful for further automation on mobile
- Runs as a Docker container on ARM64 (Raspberry Pi)
- Automatic image updates via Watchtower

## Optimization for Raspberry Pi (SD Card Longevity)

To prevent SD card degradation, the stack is pre-configured with:
- **Minimal I/O Operations:** The application and infrastructure are configured to write to the disk only when necessary.
- **Log Rotation:** Limits Docker logs to 10MB per file with a maximum of 3 archives.
- **Minimal Logging:** Watchtower is set to `LOG_LEVEL=warn` to reduce unnecessary write operations.

## Prerequisites

- **Raspberry Pi** running **Raspberry Pi OS** (64-bit recommended)
- **Docker** – install via the official Docker documentation for Raspberry Pi OS
- **Docker Compose** (plugin) – included with the Docker install above

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ser1sto/cs2-update-checker.git
cd cs2-update-checker
```

### 2. Configure environment variables

Copy the .env.template and fill in your values:

```bash
cp .env.template .env
nano .env
```

| Variable | Description |
|---|---|
| `RSS_URL` | CS2 RSS feed URL to monitor |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications |
| `USER_ID` | Discord user ID to mention in notifications |
| `TIME_THRESHOLD_MINUTES` | How often (in minutes) to look for new entries |
| `NTFY_TOPIC` | Your ntfy topic name |
| `EMAIL_ADDRESS` | Sender e-mail address |
| `EMAIL_PASSWORD` | Sender e-mail password (app password recommended) |
| `RECEIVER` | Recipient e-mail address |
| `LAST_ENTRY_PATH` | Path inside the container where the last entry is stored. Must be set to /app/data/last_entry.json to work with the default volume mapping. |

### 3. Log in to Docker Hub

The `docker-compose.yml` mounts `${HOME}/.docker/config.json` for Watchtower to authenticate with Docker Hub when pulling image updates. You must log in before starting the stack:

```bash
docker login
```

### 4. Start the stack

```bash
docker compose up -d
```

### 5. Check status

```bash
docker compose ps
#(info logs will not be shown due to log level parameter)
docker compose logs -f watchtower
```

## Automatic Updates

The stack includes Watchtower, which automatically checks for new versions of the bot image every **5 minutes** (`WATCHTOWER_POLL_INTERVAL=300`). When a new image is available, Watchtower pulls it and restarts the container with no manual intervention required. Only containers explicitly labelled with `com.centurylinklabs.watchtower.enable=true` are managed.

## CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/`) that builds and pushes a new `arm64/amd64` Docker image to Docker Hub on dispatch. Combined with Watchtower, this creates a fully automated deployment pipeline.

## Stopping the stack

```bash
docker compose down
```

## License

MIT
