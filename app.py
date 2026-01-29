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

# Error message mappings for user-friendly guidance
ERROR_MESSAGES = {
    'public_error_prominent_people_filter_failed': 'Please verify or edit any celebrity/public figure names',
    'public_error_violence_filter_failed': 'Content contains violence or harmful themes - please revise',
    'public_error_nsfw_filter_failed': 'Content flagged as inappropriate - please revise',
    'public_error_copyrighted_material': 'Content may include copyrighted material - please revise',
    'public_error_prompt_too_long': 'Prompt is too long - please shorten the text',
    'public_error_invalid_image': 'Image format or quality issue - please try a different image',
}

def parse_error_message(error_msg):
    """Convert API error codes to user-friendly messages"""
    if not error_msg:
        return "Unknown error occurred"
    
    # Check for known error patterns
    for error_code, friendly_msg in ERROR_MESSAGES.items():
        if error_code in error_msg.lower():
            return friendly_msg
    
    # Return original message if no match
    return error_msg

def parse_script(script_text):
    """Parse formatted script into segments - matches ANY label"""
    segments = []
    # Updated pattern to match any segment label (HOOK, HOOK V2, Backend 1, etc.)
    # Captures: segment label, optional "— HOLDING PRODUCT" marker, and the prompt text
    pattern = r'^([A-Z][A-Za-z0-9\s]+?)(\s*—\s*HOLDING PRODUCT)?\s*\n(.*?)(?=\n^[A-Z][A-Za-z0-9\s]+?(?:\s*—\s*HOLDING PRODUCT)?\s*\n|\Z)'
    matches = re.findall(pattern, script_text, re.DOTALL | re.MULTILINE)
    
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
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 200:
            return {'success': True, 'task_id': result.get('data', {}).get('taskId')}
        else:
            error_msg = result.get('msg', 'Unknown error')
            return {'success': False, 'error': error_msg}
    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (400, 500, etc.)
        try:
            error_data = e.response.json()
            error_msg = error_data.get('msg', str(e))
        except:
            error_msg = str(e)
        return {'success': False, 'error': f"HTTP {e.response.status_code}: {error_msg}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_status(api_key, task_id):
    """Check generation status"""
    url = f"{KIE_API_BASE}/veo/record-info"
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'taskId': task_id}
    
    try:
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
            error_msg = None
            
            if success_flag == 1 and data.get('response'):
                response_data = data['response']
                if response_data.get('resultUrls'):
                    video_url = response_data['resultUrls'][0]
            
            if success_flag in [2, 3]:
                error_msg = data.get('errorMessage', 'Generation failed')
            
            return {
                'status': status_map.get(success_flag, 'unknown'),
                'video_url': video_url,
                'error': error_msg
            }
        else:
            return {'status': 'failed', 'error': result.get('msg')}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

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
    
    if not segments:
        return jsonify({'error': 'No segments found in script. Make sure each segment starts with a label (HOOK, Backend 1, etc.)'}), 400
    
    jobs = []
    
    # Generate videos for each segment
    for seg in segments:
        # Determine which avatar to use
        if seg['holding_product']:
            if avatar_product_url:
                avatar_url = avatar_product_url
                label_suffix = " (With Product)"
            else:
                # No product avatar uploaded - skip with error
                jobs.append({
                    'label': f"{seg['label']} (With Product)",
                    'error': 'No product avatar uploaded',
                    'status': 'failed',
                    'retry_count': 0,
                    'max_retries': 3
                })
                continue
        else:
            avatar_url = avatar_normal_url
            label_suffix = ""
        
        # Attempt to generate video
        result = generate_video(api_key, seg['prompt'], avatar_url)
        
        if result['success']:
            jobs.append({
                'label': f"{seg['label']}{label_suffix}",
                'task_id': result['task_id'],
                'status': 'queued',
                'prompt': seg['prompt'],
                'avatar_url': avatar_url,
                'retry_count': 0,
                'max_retries': 3
            })
        else:
            # Initial generation failed
            jobs.append({
                'label': f"{seg['label']}{label_suffix}",
                'error': parse_error_message(result['error']),
                'raw_error': result['error'],
                'status': 'failed',
                'prompt': seg['prompt'],
                'avatar_url': avatar_url,
                'retry_count': 0,
                'max_retries': 3
            })
    
    # Save job batch
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    with open(batch_file, 'w') as f:
        json.dump({'api_key': api_key, 'jobs': jobs}, f, indent=2)
    
    return jsonify({'batch_id': batch_id, 'jobs': jobs})

@app.route('/api/status/<batch_id>', methods=['GET'])
def status(batch_id):
    """Check batch status and handle retries"""
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    if not batch_file.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    jobs = batch_data.get('jobs', [])
    api_key = batch_data.get('api_key') or request.args.get('api_key')
    
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
                
                # Handle failed jobs with retry logic
                if job['status'] == 'failed':
                    job['raw_error'] = result.get('error', 'Unknown error')
                    job['error'] = parse_error_message(job['raw_error'])
                    
                    # Attempt retry if under max retries
                    retry_count = job.get('retry_count', 0)
                    max_retries = job.get('max_retries', 3)
                    
                    if retry_count < max_retries:
                        # Retry generation
                        retry_result = generate_video(
                            api_key, 
                            job['prompt'], 
                            job['avatar_url']
                        )
                        
                        if retry_result['success']:
                            job['task_id'] = retry_result['task_id']
                            job['status'] = 'queued'
                            job['retry_count'] = retry_count + 1
                            job['error'] = None
                            job['raw_error'] = None
                        else:
                            job['retry_count'] = retry_count + 1
                            job['raw_error'] = retry_result['error']
                            job['error'] = parse_error_message(retry_result['error'])
                            if job['retry_count'] >= max_retries:
                                job['error'] = f"Failed after {max_retries} attempts: {job['error']}"
            except Exception as e:
                job['error'] = str(e)
    
    # Save updated status
    with open(batch_file, 'w') as f:
        json.dump(batch_data, f, indent=2)
    
    return jsonify({'jobs': jobs})

@app.route('/api/download/<batch_id>', methods=['POST'])
def download_batch(batch_id):
    """Download all completed videos as ZIP"""
    batch_file = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.json"
    if not batch_file.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    jobs = batch_data.get('jobs', [])
    
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
    
    if not video_files:
        return jsonify({'error': 'No completed videos to download'}), 404
    
    # Create ZIP
    zip_path = Path(app.config['OUTPUT_FOLDER']) / f"batch_{batch_id}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for video_file in video_files:
            zipf.write(video_file, video_file.name)
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
