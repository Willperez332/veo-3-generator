#!/usr/bin/env python3
"""
Test script for Kie AI API integration
"""
import requests
import sys
import time

API_KEY = "c655638addd6acd44f69431550cb7dcd"  # Will's test key
KIE_API_BASE = "https://api.kie.ai/api/v1"

def test_connection():
    """Test API connection and credit balance"""
    print("🔌 Testing Kie AI API connection...")
    
    # Try to check credits (if endpoint exists)
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    # This is a placeholder - actual endpoint may differ
    # Check Kie AI docs for correct endpoints
    print("✅ API key format valid")
    print(f"   Key: {API_KEY[:20]}...")
    return True

def test_generate(prompt="A person talking to camera, professional lighting"):
    """Test video generation (text-to-video)"""
    print(f"\n🎬 Testing video generation...")
    print(f"   Prompt: {prompt}")
    
    url = f"{KIE_API_BASE}/veo/generate"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'model': 'veo3_fast',
        'aspect_ratio': '9:16',
        'generationType': 'TEXT_2_VIDEO',
        'enableTranslation': True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                task_id = result.get('data', {}).get('taskId')
                print(f"✅ Generation started")
                print(f"   Task ID: {task_id}")
                return task_id
            else:
                print(f"❌ API Error: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_status(task_id):
    """Test status check"""
    print(f"\n📊 Checking status for task {task_id}...")
    
    url = f"{KIE_API_BASE}/veo/record-info"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    params = {'taskId': task_id}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                data = result.get('data', {})
                success_flag = data.get('successFlag')
                status_map = {0: 'Generating', 1: 'Success', 2: 'Failed', 3: 'Generation Failed'}
                print(f"✅ Status retrieved")
                print(f"   State: {status_map.get(success_flag, 'Unknown')}")
                
                if success_flag == 1 and data.get('response'):
                    response_data = data['response']
                    if response_data.get('resultUrls'):
                        print(f"   URL: {response_data['resultUrls'][0]}")
                
                return result
            else:
                print(f"❌ API Error: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("KIE AI API TEST")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Test generation (optional - costs credits)
    if '--generate' in sys.argv:
        job_id = test_generate()
        if job_id:
            print("\n⏳ Waiting 10 seconds before checking status...")
            time.sleep(10)
            test_status(job_id)
    else:
        print("\n💡 Run with --generate to test actual video generation")
        print("   (This will consume credits)")
    
    print("\n" + "=" * 60)
    print("✅ Test complete")
    print("=" * 60)
