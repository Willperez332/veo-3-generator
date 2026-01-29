# Deployment Guide

## Quick Deploy to Railway (Recommended)

Railway is the easiest option for deploying this tool.

### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Push this folder to a GitHub repo
   - In Railway: New Project → Deploy from GitHub repo
   - Select the repo
   - Railway auto-detects Python and deploys

3. **Access the App**
   - Railway provides a public URL (e.g., `https://veo-generator-production.up.railway.app`)
   - Share this URL with your team

### Alternative: Deploy from CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

---

## Deploy to Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up

2. **New Web Service**
   - Connect your GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

3. **Deploy**
   - Render builds and deploys automatically

---

## Deploy to DigitalOcean App Platform

1. **Create DigitalOcean Account**
   - Go to [digitalocean.com](https://digitalocean.com)

2. **Create App**
   - Apps → Create App → From GitHub
   - Select repo
   - Auto-detects Python

3. **Deploy**
   - DigitalOcean handles the rest

---

## Self-Hosted (VPS/Server)

If you prefer to host on your own server:

```bash
# SSH into your server
ssh user@your-server.com

# Clone repo
git clone <your-repo-url>
cd veo-generator

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Keep it running (systemd service)

Create `/etc/systemd/system/veo-generator.service`:

```ini
[Unit]
Description=VEO 3 Asset Generator
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/veo-generator
Environment="PATH=/path/to/veo-generator/venv/bin"
ExecStart=/path/to/veo-generator/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable veo-generator
sudo systemctl start veo-generator
```

---

## Environment Variables (Optional)

None required! Each user provides their own Kie AI API key in the UI.

---

## DNS & SSL

Once deployed, you can:
1. Point a custom domain to the deployment
2. Enable HTTPS (Railway/Render do this automatically)

Example: `https://veo.youragency.com`

---

## Team Access

Once deployed, share the URL with your team:
- They open the URL
- Enter their own Kie AI API key
- Paste scripts and generate videos

Each team member can work independently with their own API key.
