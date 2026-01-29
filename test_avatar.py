#!/usr/bin/env python3
"""
Test avatar image-to-video generation
"""
import requests
import time
import sys

API_KEY = "c655638addd6acd44f69431550cb7dcd"
KIE_API_BASE = "https://api.kie.ai/api/v1"
UPLOAD_BASE = "https://kieai.redpandaai.co"

test_prompt = """NO CAPTIONS ON SCREEN. NO CAMERA MOVEMENTS. NO EDITS. NO BACKGROUND MUSIC. Handheld phone video style. Make the avatar say in a validating, slightly surprised tone: "She's actually not entirely wrong. Parasites are more common than people think." """

def upload_avatar():
    """Upload avatar image and return URL"""
    print("📤 Uploading avatar image...")
    
    url = f"{UPLOAD_BASE}/api/file-stream-upload"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    with open('avatar.jpg', 'rb') as f:
        files = {'file': ('avatar.jpg', f, 'image/jpeg')}
        data = {'uploadPath': 'avatars'}
        response = requests.post(url, headers=headers, files=files, data=data)
    
    result = response.json()
    
    if result.get('success') and result.get('code') == 200:
        data = result.get('data', {})
        file_url = data.get('downloadUrl')
        if file_url:
            print(f"✅ Avatar uploaded!")
            print(f"   URL: {file_url}")
            return file_url
        else:
            print(f"❌ No downloadUrl in response")
            return None
    else:
        print(f"❌ Upload failed: {result.get('msg')}")
        return None

def generate_video_with_avatar(prompt, avatar_url):
    """Generate video with avatar image"""
    print(f"\n🎬 Generating video with avatar...")
    print(f"   Avatar: {avatar_url}")
    print(f"   Prompt: {prompt[:80]}...")
    
    url = f"{KIE_API_BASE}/veo/generate"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'model': 'veo3_fast',
        'aspect_ratio': '9:16',
        'imageUrls': [avatar_url],
        'generationType': 'FIRST_AND_LAST_FRAMES_2_VIDEO',
        'enableTranslation': True
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get('code') == 200:
        task_id = result.get('data', {}).get('taskId')
        print(f"✅ Generation started!")
        print(f"   Task ID: {task_id}")
        return task_id
    else:
        print(f"❌ Error: {result.get('msg')}")
        return None

def check_status(task_id):
    """Check generation status"""
    url = f"{KIE_API_BASE}/veo/record-info"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    params = {'taskId': task_id}
    
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    
    if result.get('code') == 200:
        data = result.get('data', {})
        success_flag = data.get('successFlag')
        status_map = {0: 'Generating', 1: 'Success', 2: 'Failed', 3: 'Generation Failed'}
        
        status = status_map.get(success_flag, 'Unknown')
        
        video_url = None
        if success_flag == 1 and data.get('response'):
            response_data = data['response']
            if response_data.get('resultUrls'):
                video_url = response_data['resultUrls'][0]
        
        return {
            'status': status,
            'video_url': video_url,
            'success_flag': success_flag
        }
    else:
        return {'status': 'Error', 'success_flag': -1}

if __name__ == '__main__':
    print("=" * 60)
    print("VEO 3 AVATAR TEST")
    print("=" * 60)
    
    # Step 1: Upload avatar
    avatar_url = upload_avatar()
    if not avatar_url:
        print("❌ Cannot proceed without avatar upload")
        sys.exit(1)
    
    # Step 2: Generate video with avatar
    task_id = generate_video_with_avatar(test_prompt, avatar_url)
    if not task_id:
        sys.exit(1)
    
    print("\n⏳ Monitoring generation (this takes ~60-90 seconds)...")
    print("   (You can Ctrl+C and check later)\n")
    
    # Poll status every 10 seconds
    last_status = None
    while True:
        try:
            time.sleep(10)
            result = check_status(task_id)
            
            if result['status'] != last_status:
                print(f"📊 Status: {result['status']}")
                last_status = result['status']
            
            if result['success_flag'] == 1:
                print(f"\n✅ VIDEO READY!")
                print(f"📹 URL: {result['video_url']}")
                print("\n" + "=" * 60)
                break
            elif result['success_flag'] in [2, 3]:
                print(f"\n❌ Generation failed")
                print("\n" + "=" * 60)
                break
                
        except KeyboardInterrupt:
            print(f"\n\n💡 Generation still running in background")
            print(f"   Task ID: {task_id}")
            break
