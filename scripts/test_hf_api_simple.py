"""Simple test of Hugging Face API"""
import requests
import os

API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_TOKEN_HERE")
# Try different models and endpoints
API_URLS = [
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
    "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
]

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "a red t-shirt on white background, product photography",
    "parameters": {
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }
}

print("Testing Hugging Face API...")
print(f"Token: {API_TOKEN[:10]}...")

for API_URL in API_URLS:
    print(f"\nTrying URL: {API_URL}")
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("\n[SUCCESS] API is working! Saving test image...")
            with open("test_hf_image.png", "wb") as f:
                f.write(response.content)
            print("Test image saved to test_hf_image.png")
            break
        elif response.status_code == 503:
            print("[INFO] Model is loading (503) - this is normal for first request")
            print(f"Response: {response.text[:500]}")
        elif response.status_code == 429:
            print("[INFO] Rate limited (429)")
            print(f"Response: {response.text[:500]}")
        elif response.status_code == 410:
            print(f"[INFO] Endpoint deprecated: {response.text[:200]}")
            continue
        else:
            print(f"[ERROR] Unexpected status code")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        continue

