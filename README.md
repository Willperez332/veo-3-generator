# VEO 3 Asset Generator

Batch generate VEO 3 videos from formatted scripts via Kie AI API.

## Features

- Parse formatted scripts (Backend 1, Backend 2, etc.)
- Generate two versions per segment:
  - Avatar only (no product)
  - Avatar + product
- 9:16 aspect ratio (vertical video)
- Real-time progress tracking
- Batch download as ZIP
- Each user brings their own Kie AI API key

## Setup

### 1. Install Dependencies

```bash
cd assets/veo-generator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add Avatar Image

Place your avatar image at:
```
assets/veo-generator/avatar.jpg
```

(Optional) Add product image:
```
assets/veo-generator/product.jpg
```

### 3. Run Locally

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python -m flask run --host=0.0.0.0 --port=8000
```

Open http://localhost:8000 in your browser.

## Usage

1. **Enter API Key** - Your Kie AI API key (saved in browser)
2. **Paste Script** - Formatted script with "Backend 1", "Backend 2", etc.
3. **Generate** - Starts batch generation
4. **Monitor** - Real-time status updates
5. **Download** - Get all videos as ZIP when complete

## Script Format Example

```
Backend 1 
NO CAPTIONS ON SCREEN. NO CAMERA MOVEMENTS. NO EDITS. NO BACKGROUND MUSIC. Handheld phone video style. Make the avatar say in a validating, slightly surprised tone: "She's actually not entirely wrong. Parasites are more common than people think."

Backend 2 
NO CAPTIONS ON SCREEN. NO CAMERA MOVEMENTS. NO EDITS. NO BACKGROUND MUSIC. Handheld phone video style. Make the avatar say in an informative, confirming tone: "Teeth grinding, sugar cravings, trouble sleeping..."
```

## Deploy to Server

### Railway (Recommended)

1. Create account at railway.app
2. New Project → Deploy from GitHub
3. Add environment variables if needed
4. Deploy

### Render

1. Create account at render.com
2. New Web Service → Connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python app.py`
5. Deploy

### DigitalOcean

1. Create Droplet (Ubuntu)
2. SSH in and clone repo
3. Install dependencies
4. Run with gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

## API Endpoints

- `POST /api/generate` - Start batch generation
- `GET /api/status/<batch_id>` - Check status
- `POST /api/download/<batch_id>` - Download ZIP

## Notes

- Each video generation costs ~60 credits ($0.30) on Kie AI
- Status polls every 5 seconds
- Videos download automatically when complete
- Avatar image required, product image optional
