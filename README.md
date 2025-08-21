# 🔄 CS2 Update Checker (Dockerized for Raspberry Pi)

This application runs on a Raspberry Pi and checks every 15 minutes for updates to **Counter-Strike 2 (CS2)**.

It is designed to be **lightweight**, **automated**, and **easily deployable** using Docker and cron.

---

## 📦 How It Works

- A cron job runs every **15 minutes** on the Raspberry Pi.
- The job:
  1. 🛳️ Pulls the latest Docker image from Docker Hub
  2. 🚀 Runs the container using the `.env` file - necessary variables can be found in .env.template
- The container performs the update check and exits.

---

## 🔔 Enable Mobile Notifiaction

1. Install the ntfy app on your phone (Android & iOS)
2. Subscribe to your chosen topic defined in .env 
- Push notification will be sent if armory is mentioned in release notes.

---

## 🛠️ Build the image

``` docker build -t test-app . ```

## 🧪 Run & Test Locally

``` docker run --rm -it --env-file .env test-app ```
