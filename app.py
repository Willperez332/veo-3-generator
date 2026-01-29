#!/usr/bin/env python3
"""
VEO 3 Asset Generator - Batch video generation via Kie AI
"""
import os
import re
import time
import json
import requests
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from pathlib import Path
import zipfile
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Kie AI API endpoint
KIE_API_BASE = "https://api.kie.ai/api/v1"

def parse_script(script_text):
    """Parse formatted script into segments"""
    segments = []
    # Updated pattern to capture "HOLDING PRODUCT" marker
    pattern = r'(Backend \d+|Hook)(\s*—\s*HOLDING PRODUCT)?\s*\n(.*?)(?=\n(?:Backend \d+|Hook)|$)'
    matches = re.findall(pattern, script_text, re.DOTALL)
    
    for label, holding_product, prompt in matches:
        segments.append({
            'label': label.strip(),
            'prompt': prompt.strip(),
            'holding_product': bool(holding_product)
        })
    
    return segments

def upload_image(api_key, image_path):
    """Upload image to Kie AI and return URL"""
    url = "https://kieai.redpandaai.co/api/file-stream-upload"
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            data = {'uploadPath': 'avatars'}
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and result.get('code') == 200:
                return result.get('data', {}).get('downloadUrl')
            else:
                print(f"Upload error: {result.get('msg')}")
                return None
    except Exception as e:
        print(f"Upload exception: {e}")
        return None

def generate_video(api_key, prompt, image_url=None, aspect_ratio="9:16"):
    """Generate video via Kie AI API"""
    url = f"{KIE_API_BASE}/veo/generate"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'prompt': prompt,
        'model': 'veo3_fast',
        'aspect_ratio': aspect_ratio,
        'enableTranslation': True
    }
    
    if image_url:
        data['imageUrls'] = [image_url]
        data['generationType'] = 'FIRST_AND_LAST_FRAMES_2_VIDEO'
    else:
        data['generationType'] = 'TEXT_2_VIDEO'
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    
    if result.get('code') == 200:
        return result.get('data', {}).get('taskId')
    else:
        raise Exception(f"API Error: {result.get('msg')}")

def check_status(api_key, task_id):
    """Check generation status"""
    url = f"{KIE_API_BASE}/veo/record-info"
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'taskId': task_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    result = response.json()
    
    if result.get('code') == 200:
        data = result.get('data', {})
        success_flag = data.get('successFlag')
        
        # Map successFlag to status
        status_map = {
            0: 'generating',
            1: 'completed',
            2: 'failed',
            3: 'failed'
        }
        
        video_url = None
        if success_flag == 1 and data.get('response'):
            response_data = data['response']
            if response_data.get('resultUrls'):
                video_url = response_data['resultUrls'][0]
        
        return {
            'status': status_map.get(success_flag, 'unknown'),
            'video_url': video_url,
            'error': data.get('errorMessage') if success_flag in [2, 3] else None
        }
    else:
        return {'status': 'failed', 'error': result.get('msg')}

def download_video(video_url, output_path):
    """Download generated video"""
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-avatar', methods=['POST'])
def upload_avatar_endpoint():
    """Upload avatar image and return URL"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    api_key = request.form.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 400
    
    # Save file temporarily
    temp_path = Path(app.config['UPLOAD_FOLDER']) / f"avatar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    file.save(temp_path)
    
    try:
        # Upload to Kie AI
        avatar_url = upload_image(api_key, str(temp_path))
        if not avatar_url:
            return jsonify({'error': 'Failed to upload avatar to Kie AI'}), 500
        
        return jsonify({'avatar_url': avatar_url})
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start batch generation"""
    data = request.json
    api_key = data.get('api_key')
    script = data.get('script')
    avatar_normal_url = data.get('avatar_normal_url')
    avatar_product_url = data.get('avatar_product_url')
    
    if not api_key or not script or not avatar_normal_url:
        return jsonify({'error': 'Missing API key, script, or normal avatar URL'}), 400
    
    segments = parse_script(script)
    jobs = []
    
    # Generate videos for each segment
    for seg in segments:
        if seg['holding_product']:
            # HOLDING PRODUCT segment - use product avatar if available
            if avatar_product_url:
                try:
                    task_id = generate_video(api_key, seg['prompt'], avatar_product_url)
                    jobs.append({
                        'label': f"{seg['label']} (With Product)",
                        'task_id': task_id,
                        'status': 'queued',
                        'type': 'product'
                    })
                except Exception as e:
                    jobs.append({
                        'label': f"{seg['label']} (With Product)",
                        'error': str(e),
                        'status': 'failed',
                        'type': 'product'
                    })
            else:
                # No product avatar uploaded - skip or warn
                jobs.append({
                    'label': f"{seg['label']} (With Product)",
                    'error': 'No product avatar uploaded',
                    'status': 'failed',
                    'type': 'product'
                })
        else:
            # Normal segment - use normal avatar
            try:
                task_id = generate_video(api_key, seg['prompt'], avatar_normal_url)
                jobs.append({
                    'label': f"{seg['label']}",
                    'task_id': task_id,
                    'status': 'queued',
                    'type': 'normal'
                })
            except Exception as e:
                jobs.append({
                    'label': f"{seg['label']}",
                    'error': str(e),
                    'status': 'failed',
                    'type': 'normal'
                })
    
    # Save job batch
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    with open(batch_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    return jsonify({'batch_id': batch_id, 'jobs': jobs})

@app.route('/api/status/<batch_id>', methods=['GET'])
def status(batch_id):
    """Check batch status"""
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    if not batch_file.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    with open(batch_file, 'r') as f:
        jobs = json.load(f)
    
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 400
    
    # Update status for each job
    for job in jobs:
        if job.get('status') in ['queued', 'generating'] and job.get('task_id'):
            try:
                result = check_status(api_key, job['task_id'])
                job['status'] = result.get('status', 'unknown')
                if result.get('video_url'):
                    job['video_url'] = result['video_url']
            except Exception as e:
                job['error'] = str(e)
    
    # Save updated status
    with open(batch_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    return jsonify({'jobs': jobs})

@app.route('/api/download/<batch_id>', methods=['POST'])
def download_batch(batch_id):
    """Download all completed videos as ZIP"""
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    if not batch_file.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    with open(batch_file, 'r') as f:
        jobs = json.load(f)
    
    # Download all completed videos
    video_files = []
    for job in jobs:
        if job.get('status') == 'completed' and job.get('video_url'):
            filename = f"{job['label'].replace(' ', '_')}.mp4"
            filepath = Path(app.config['OUTPUT_FOLDER']) / filename
            try:
                download_video(job['video_url'], filepath)
                video_files.append(filepath)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
    
    # Create ZIP
    zip_path = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for video_file in video_files:
            zipf.write(video_file, video_file.name)
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
