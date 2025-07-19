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

## 🛠️ Build the image

``` docker build -t test-app . ```

## 🧪 Run & Test Locally

``` docker run --rm -it --env-file .env test-app ```
