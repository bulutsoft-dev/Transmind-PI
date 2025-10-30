# Transmind-PI — Setup & Troubleshooting Guide

This document is a practical, copy-paste friendly guide to install, run and troubleshoot the Flask + Picamera2 MJPEG streamer on a Raspberry Pi (or a similar Debian-based device).

It also includes exact commands for the issues you hit in your logs ("Device or resource busy", missing `picamera2`/`libcamera`, and `libcap-dev` build headers).

---

## Quick summary

- Use hardware JPEG via Picamera2 (good: low CPU).
- Keep camera initialization in one process — run Gunicorn with a single worker to avoid "Device or resource busy".
- Use `gevent` worker class so that the single process can serve many concurrent clients.
- If `pip install picamera2` fails with `python-prctl` errors, install `libcap-dev` first.
- If Python complains `No module named 'libcamera'`, install `python3-libcamera` via apt.

---

## 0) Preconditions / assumptions

- Running Raspberry Pi OS (or Debian-based OS) with SSH access.
- Camera hardware connected to the CSI port and enabled via `raspi-config` (Legacy Camera / Interface Options -> Enable when required).

---

## 1) System-level install (copy/paste)

Open an SSH session to the Pi and run the following (in order):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-libcamera libcap-dev
```

Notes:
- `python3-picamera2` and `python3-libcamera` provide the system bindings for libcamera/picamera2.
- `libcap-dev` fixes the `python-prctl` build error that `pip` sometimes raises when installing `picamera2`.

If you previously tried `pip install picamera2` and saw build errors, installing `libcap-dev` then re-running pip will typically fix it.

---

## 2) Project layout (recommended)

Create a project folder and a Python virtual environment:

```bash
mkdir -p ~/stream_project
cd ~/stream_project
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

Install Python requirements inside the venv:

```bash
pip install Flask gunicorn gevent
# If you still need it in the venv: pip install picamera2
```

Your repo already contains an `app.py` that uses a global `camera = Picamera2()` — that is correct (camera must be opened by the single process that uses it).

---

## 3) Recommended `app.py` considerations

- Keep `camera = Picamera2()` in module-global scope (outside `if __name__ == '__main__'`) so the running process opens it once.
- Use hardware JPEG via `camera.capture_file(stream, format='jpeg')` (this keeps CPU low).
- Lower resolution to increase FPS: `main={"size": (640, 480)}` or lower.
- Use a streaming endpoint that yields MJPEG frames and `multipart/x-mixed-replace` mime-type.

Your `app.py` already follows this pattern. Example run-time command below.

---

## 4) Run server (production recommended command)

Because only one process can open the camera, we run Gunicorn with 1 worker; to support many concurrent clients, choose an async worker class (`gevent`).

Activate your venv and run:

```bash
source ~/stream_project/venv/bin/activate
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
```

Why this exact command:
- `--workers 1`: prevents multiple processes trying to acquire the camera resource.
- `--worker-class gevent`: allows that single process to serve many concurrent streaming clients efficiently.

Test locally from another machine on your network:

```bash
# open in browser or an <img> tag pointing to
http://<RPI_IP>:5000/stream
# or the route you implemented (e.g. /video_feed)
```

---

## 5) Optional: systemd service (auto-start on boot)

Create `/etc/systemd/system/stream.service` and edit `User`, `WorkingDirectory`, and `ExecStart` to match your paths. Example (adjust `/home/pi/stream_project` and `pi` to your user & path):

```ini
[Unit]
Description=Gunicorn Video Stream Server
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/stream_project
ExecStart=/home/pi/stream_project/venv/bin/gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable stream.service
sudo systemctl start stream.service
sudo systemctl status stream.service
# Follow logs
sudo journalctl -u stream.service -f
```

---

## 6) Troubleshooting — direct mappings to your logs

1) "Device or resource busy" / `Failed to acquire camera`
- Symptom: Gunicorn starts multiple workers and most crash with `Failed to acquire camera: Device or resource busy`.
- Cause: Multiple processes try to open a single camera device.
- Fix: Run Gunicorn with a single worker and a concurrent worker-class: `gunicorn --worker-class gevent --workers 1 ...`.

2) `ModuleNotFoundError: No module named 'picamera2'` when running Gunicorn
- Symptom: Worker fails to boot, complaining about missing `picamera2`.
- Cause: `picamera2` not installed in the environment used by Gunicorn (or you installed system package but running a venv without it).
- Fix: Activate the same venv used by Gunicorn and run `pip install picamera2`. Alternatively, use `sudo apt install python3-picamera2`.

3) `You need to install libcap development headers to build this module` (during `pip install picamera2`)
- Symptom: `pip` fails while building `python-prctl`.
- Fix: `sudo apt install libcap-dev` then re-run `pip install picamera2`.

4) `ModuleNotFoundError: No module named 'libcamera'`
- Symptom: `picamera2` imports fail because `libcamera` Python bindings are not present.
- Fix: `sudo apt install python3-libcamera` (system package).

---

## 7) Exposing the stream to the Internet (short options)

- Quick and temporary: `ngrok` or `cloudflared` (easy for testing; ngrok URL changes unless you have a paid plan).
- Secure and stable: `Tailscale` or `ZeroTier` — create a mesh VPN and use the Pi's virtual IP.
- Direct: Router port forwarding + DDNS (No-IP / DuckDNS) — requires router access and security hardening.

Example (ngrok):

```bash
# after downloading ngrok and authenticating
./ngrok http 5000
# ngrok will give you a public URL that forwards to your local server
```

---

## 8) Performance tuning tips

- Lower resolution (biggest FPS win): `640x480` → `320x240` if you need speed.
- Reduce JPEG quality if supported to lower transfer size and increase throughput.
- Use a CDN, relay or WebRTC if you expect many remote viewers (for scale and latency improvements).
- If CPU usage is still critical and you need absolute minimal overhead, consider a C/C++ server using libcamera and a lightweight HTTP server — but only if you need that last 10–30%.

---

## 9) Quick check-list (copy/paste)

```bash
# system prereqs (run once)
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-libcamera libcap-dev

# project setup
mkdir -p ~/stream_project && cd ~/stream_project
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Flask gunicorn gevent
# optional (only if needed in your venv): pip install picamera2

# run (single worker + gevent)
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
```

---

## 10) If something still fails

Paste the exact error lines from the Gunicorn worker log (the stacktrace) here. I can map them to the right fix quickly. The most common next steps are:
- Ensure you are activating the same venv that contains the installed packages before launching Gunicorn.
- If a build step fails during pip, install the missing system dev package (`libcap-dev`, `libffi-dev`, `libssl-dev` etc.) then retry.

---

If you want, I can also:
- Create/update a `systemd` service file in this repo with your actual username & paths.
- Add a small status route (`/health`) to `app.py` that checks camera availability.
- Add a `requirements.txt` pinned file for your venv.

Tell me which of those you'd like and I'll apply them.
