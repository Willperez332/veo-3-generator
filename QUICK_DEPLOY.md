# Quick Deploy to Railway

## ✅ What's Updated

- Users can now upload their own avatar image in the UI
- Script parser detects "— HOLDING PRODUCT" marker
- Generates 2 videos for HOLDING PRODUCT segments (normal + with product)
- Generates 1 video for normal segments

## Step-by-Step Deployment

### 1. Create GitHub Repo

Go to: https://github.com/new

- Repository name: `veo-3-generator`
- Description: `Batch VEO 3 video generator for Operation Moonscale`
- Visibility: Public or Private (your choice)
- Click "Create repository"

### 2. Push Code to GitHub

Copy the commands from the "…or push an existing repository from the command line" section.

It will look like this:

```bash
cd /Users/williamperez/clawd/assets/veo-generator
git remote add origin https://github.com/Willperez332/veo-3-generator.git
git branch -M main
git push -u origin main
```

Run those commands in your terminal.

### 3. Deploy to Railway

Go to: https://railway.com/dashboard

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `veo-3-generator` from the list
4. Railway will auto-detect Python and deploy
5. Wait 2-3 minutes for build to complete
6. Click "Settings" → "Generate Domain"
7. Copy the public URL (e.g., `https://veo-3-generator-production.up.railway.app`)

### 4. Share with Team

Send them the Railway URL. They will:
1. Open the URL
2. Enter their Kie AI API key
3. Upload their avatar image
4. Paste their formatted script
5. Click "Generate Videos"

---

## Example Script Format

```
Backend 1
NO CAPTIONS ON SCREEN. NO CAMERA MOVEMENTS. NO EDITS. NO BACKGROUND MUSIC. Handheld phone video style. Make the avatar say in a validating tone: "She's not wrong..."

Backend 2 — HOLDING PRODUCT
NO CAPTIONS ON SCREEN. NO CAMERA MOVEMENTS. NO EDITS. NO BACKGROUND MUSIC. Handheld phone video style. Make the avatar say with the product: "This one from Micro Ingredients..."
```

**Result:**
- Backend 1: 1 video (normal)
- Backend 2: 2 videos (normal + with product)

---

## That's It!

Once deployed, the tool is live and ready for the team to use.

Each person uses their own API key. No shared infrastructure needed.
