# Deployment Guide — Putting School Hub Online (24/7)

This guide takes you from "running on my own laptop" to "live on a VPS, accessible
from any phone/browser, for all your school clients."

---

## 1. Get a VPS

Pick any provider with a plan around **PKR 2,000–3,000/month** (2 vCPU, 2–4GB RAM,
Ubuntu 22.04 or 24.04). Hostinger, Contabo, and DigitalOcean are all reasonable options.

You'll get an **IP address** and root SSH access.

---

## 2. Connect and install prerequisites

```bash
ssh root@YOUR_SERVER_IP

apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx git
```

---

## 3. Get the code onto the server

```bash
cd /opt
git clone https://github.com/sohail2365/schoolhub.git
cd schoolhub
```

---

## 4. Set up the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Generate a real production `.env`

**Do not skip this** — the codebase ships with a placeholder JWT secret that is
publicly visible in the repo. Without this step, anyone could forge login
tokens for any school on your server.

```bash
python backend/generate_env.py
```

This creates `backend/.env` with a strong, randomly generated secret. It will
refuse to overwrite an existing `.env`, so it's safe to run again by accident.

---

## 6. Run it as a background service (systemd)

Create `/etc/systemd/system/schoolhub.service`:

```ini
[Unit]
Description=School Hub FastAPI app
After=network.target

[Service]
User=root
WorkingDirectory=/opt/schoolhub
ExecStart=/opt/schoolhub/.venv/bin/python -m backend.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
systemctl daemon-reload
systemctl enable schoolhub
systemctl start schoolhub
systemctl status schoolhub   # should show "active (running)"
```

This makes the app **auto-restart** if it crashes, and **auto-start** if the
server reboots. The app listens on port 8000 internally.

---

## 7. Put Nginx in front of it (so it's on port 80/443, not 8000)

Create `/etc/nginx/sites-available/schoolhub`:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/schoolhub /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

At this point, visiting `http://YOUR_SERVER_IP/login.html` in a browser should load the app.

---

## 8. (Recommended) Add a domain + free SSL

Point a domain's DNS A record at your server IP, then:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

This gets you free HTTPS (auto-renews). Update the Nginx config's
`server_name` to your domain instead of the IP.

**Why this matters:** WhatsApp reminder links and general password security
work better over HTTPS, and clients trust a real domain more than a bare IP.

---

## 9. Set up automated daily backups

Since this is multi-tenant (all schools' data in one `school.db` file), a
backup protects **every client at once** — this isn't optional.

```bash
crontab -e
```

Add this line (runs daily at 2 AM):

```
0 2 * * * cd /opt/schoolhub && /opt/schoolhub/.venv/bin/python backend/backup_db.py >> /opt/schoolhub/logs/backup.log 2>&1
```

Backups land in `/opt/schoolhub/backups/`, timestamped, with anything older
than 14 days auto-deleted. Periodically copy these off the server too (e.g.
download to your own laptop weekly) — a backup that lives only on the same
server doesn't protect you if the whole server is lost.

---

## 10. Deploying updates later

When you push new code changes to GitHub:

```bash
cd /opt/schoolhub
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt   # only if requirements changed
systemctl restart schoolhub
```

---

## Quick troubleshooting

- **App not responding:** `systemctl status schoolhub` and `journalctl -u schoolhub -n 50`
- **Nginx errors:** `nginx -t` to check config, `systemctl status nginx`
- **Database looks wrong:** check `backend/.env` points to the right `DATABASE_URL`, and confirm you're not accidentally running two copies of the app on different ports
