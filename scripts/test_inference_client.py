"""Test InferenceClient directly"""
from huggingface_hub import InferenceClient
import os

API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_TOKEN_HERE")

print("Testing InferenceClient...")
try:
    client = InferenceClient(token=API_TOKEN)
    print("Client initialized")
    
    prompt = "a red t-shirt on white background, product photography"
    print(f"Prompt: {prompt}")
    print("Calling text_to_image...")
    
    result = client.text_to_image(
        prompt,
        model="runwayml/stable-diffusion-v1-5",
        num_inference_steps=20,
        guidance_scale=7.5
    )
    
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    if isinstance(result, bytes):
        print(f"Got bytes: {len(result)} bytes")
        with open("test_client_image.png", "wb") as f:
            f.write(result)
        print("Saved to test_client_image.png")
    elif hasattr(result, 'save'):
        print("Got PIL Image")
        result.save("test_client_image.png")
        print("Saved to test_client_image.png")
    else:
        print(f"Unexpected result type")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

